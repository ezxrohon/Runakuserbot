"""🫧🦋 ʀuɴAk userbot — entry point."""
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logging.getLogger("telethon").setLevel(logging.WARNING)
log = logging.getLogger("runak")


async def main():
    missing = cfg.missing_required()
    if missing:
        raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")

    # Bind the health port first so Render marks the service healthy quickly.
    background = [asyncio.create_task(health.serve()), asyncio.create_task(health.keepalive())]

    client = TelegramClient(StringSession(cfg.SESSION), cfg.API_ID, cfg.API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        raise SystemExit("TELEGRAM_SESSION is not authorized. Create a new one with create_session.py.")
    me = await client.get_me()

    store = Store()
    await store.load(client)
    ctx = Ctx(client, store, me)

    for module in ALL:
        module.setup(ctx)
        ctx.registry.append(module)
    log.info("Loaded plugins: %s", ", ".join(m.NAME for m in ctx.registry))

    if cfg.BOT_TOKEN:
        try:
            bot = TelegramClient(StringSession(), cfg.API_ID, cfg.API_HASH)
            await bot.start(bot_token=cfg.BOT_TOKEN)
            ctx.bot = bot
            panel.setup(ctx)
            log.info("Control panel ready: @%s", (await bot.get_me()).username)
        except Exception:
            log.exception("Control panel failed to start; continuing without it")
    else:
        log.warning("BOT_TOKEN not set — running without the control panel")

    log.info("%s is online as %s (%s)", BRAND, me.first_name, me.id)
    try:
        await client.run_until_disconnected()
    finally:
        for task in background + ctx.tasks:
            task.cancel()
        await store.flush()


if __name__ == "__main__":
    asyncio.run(main())
