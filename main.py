"""🫧🦋 ʀuɴAk userbot — entry point. Runs one or more of your own accounts at once."""
import asyncio
import logging

from telethon import TelegramClient
from telethon.sessions import StringSession

from runak import config as cfg
from runak import health, panel
from runak.branding import BRAND
from runak.context import Ctx
from runak.plugins import ALL
from runak.store import Store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("telethon").setLevel(logging.WARNING)
log = logging.getLogger("runak")


async def start_account(session: str, index: int) -> Ctx | None:
    client = TelegramClient(StringSession(session), cfg.API_ID, cfg.API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        log.error("Account #%d: session is not authorized — skipping it. Re-run create_session.py.", index + 1)
        await client.disconnect()
        return None
    me = await client.get_me()
    store = Store(str(me.id))
    await store.load(client)
    ctx = Ctx(client, store, me)
    for module in ALL:
        module.setup(ctx)
        ctx.registry.append(module)
    log.info("Account #%d online as %s (%s) — plugins: %s", index + 1, me.first_name, me.id,
             ", ".join(m.NAME for m in ctx.registry))
    return ctx


async def main():
    missing = cfg.missing_required()
    if missing:
        raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")
    background = [asyncio.create_task(health.serve()), asyncio.create_task(health.keepalive())]
    dynamic_account_tasks = set()
    results = await asyncio.gather(*(start_account(s, i) for i, s in enumerate(cfg.SESSIONS)))
    ctxs = [c for c in results if c is not None]
    if not ctxs:
        raise SystemExit("No account session was valid. Check TELEGRAM_SESSION(S).")

    async def add_account(session: str):
        new_ctx = await start_account(session, len(ctxs))
        if new_ctx is None or any(c.me.id == new_ctx.me.id for c in ctxs):
            if new_ctx is not None:
                await new_ctx.client.disconnect()
            return None
        ctxs.append(new_ctx)
        task = asyncio.create_task(new_ctx.client.run_until_disconnected())
        dynamic_account_tasks.add(task)
        task.add_done_callback(dynamic_account_tasks.discard)
        return new_ctx

    if cfg.BOT_TOKEN:
        try:
            bot = TelegramClient(StringSession(), cfg.API_ID, cfg.API_HASH)
            await bot.start(bot_token=cfg.BOT_TOKEN)
            for ctx in ctxs:
                ctx.bot = bot
            panel.setup(bot, ctxs, add_account=add_account)
            log.info("Control panel ready: @%s (%d account%s)", (await bot.get_me()).username,
                     len(ctxs), "" if len(ctxs) == 1 else "s")
        except Exception:
            log.exception("Control panel failed to start; continuing without it")
    else:
        log.warning("BOT_TOKEN not set — running without the control panel")

    log.info("%s is online — %d account%s connected", BRAND, len(ctxs), "" if len(ctxs) == 1 else "s")
    try:
        await asyncio.gather(*(c.client.run_until_disconnected() for c in ctxs))
    finally:
        for task in background:
            task.cancel()
        for task in dynamic_account_tasks:
            task.cancel()
        for ctx in ctxs:
            for task in ctx.tasks:
                task.cancel()
            await ctx.store.flush()


if __name__ == "__main__":
    asyncio.run(main())
