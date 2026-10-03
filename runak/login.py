"""Self-service login through the bot: one login -> two sessions (Telethon + Pyrogram).

Flow: /login -> consent -> phone -> code -> (2FA password) -> done. The Telethon session runs the
userbot; a second, independent session (own auth key) is packed as a Pyrogram string for voice-chat
features. Both are stored encrypted (see vault.py). /logout revokes and deletes everything.

Safety rules baked in: explicit consent screen, login code/2FA password only held in memory during
the flow (and the user's password message is deleted), nothing secret is ever logged, and a hosted
user can only ever control their OWN account (they never get the owner control panel).
"""
import asyncio
import logging
import re
import time
from datetime import datetime, timezone

from telethon import Button, TelegramClient, events
from telethon.sessions import StringSession

from . import access, helpmenu, vault
from . import config as cfg
from .branding import BRAND

log = logging.getLogger("runak.login")

FLOW_TTL = 600  # seconds a half-finished login is kept

CONSENT = (
    f"**🔐 {BRAND} — Login**\n\n"
    "By continuing you agree that:\n"
    "• this server will run a userbot **on your own account** (it acts only through your own outgoing messages)\n"
    "• two session strings are created from your login and stored **encrypted**\n"
    "• your name and user ID may be posted to the hosted-users log\n"
    "• `/logout` ends both sessions and deletes everything, any time\n\n"
    "⚠️ Never share your login code or 2FA password with anyone else. Only enter them here, in this chat.\n\n"
    "Continue?"
)


def _digits(text: str) -> str:
    return re.sub(r"\D", "", text or "")


async def second_session(client, me, password: str | None):
    """Create an independent session through QR approval and pack it as a Pyrogram string.

    Returns (pyrogram_string, session_hash) or (None, None) if it couldn't be made — the Telethon
    session still works fine without it.
    """
    from telethon.errors import SessionPasswordNeededError
    from telethon.tl.functions.account import GetAuthorizationsRequest
    from telethon.tl.functions.auth import AcceptLoginTokenRequest

    other = TelegramClient(StringSession(), cfg.API_ID, cfg.API_HASH)
    try:
        await other.connect()
        qr = await other.qr_login()
        await client(AcceptLoginTokenRequest(token=qr.token))
        try:
            await qr.wait(30)
        except SessionPasswordNeededError:
            if not password:
                return None, None
            await other.sign_in(password=password)
        session_hash = None
        try:
            auths = await other(GetAuthorizationsRequest())
            session_hash = next((a.hash for a in auths.authorizations if a.current), None)
        except Exception:
            log.warning("Could not read the second session's hash; /logout can't revoke it automatically")
        packed = vault.pyrogram_string(other.session.dc_id, cfg.API_ID, other.session.auth_key.key, me.id)
        return packed, session_hash
    except Exception as exc:
        log.warning("Second (Pyrogram) session not created: %s", type(exc).__name__)
        return None, None
    finally:
        try:
            await other.disconnect()
        except Exception:
            pass


def setup(bot, start_account, hosted: dict, tasks: set):
    """Register /login, /logout and their buttons on the bot. `hosted` maps user id -> Ctx."""
    flows: dict[int, dict] = {}

    def fresh(uid):
        flow = flows.get(uid)
        if flow and time.time() - flow["ts"] > FLOW_TTL:
            drop(uid)
            return None
        return flow

    def drop(uid):
        flow = flows.pop(uid, None)
        if flow and flow.get("client"):
            asyncio.ensure_future(_quiet_disconnect(flow["client"]))

    async def _quiet_disconnect(client):
        try:
            await client.disconnect()
        except Exception:
            pass

    async def begin(event):
        uid = event.sender_id
        if not access.allowed(uid):
            await helpmenu.send_denied(event)
            return
        if not vault.enabled():
            await event.respond("🔒 Public login isn't enabled on this deployer.")
            return
        if uid in hosted:
            await event.respond("✅ Your userbot is already running. Send /logout to remove it.")
            return
        if len(hosted) >= cfg.MAX_HOSTED:
            await event.respond("🚫 This deployer is full right now. Try again later.")
            return
        drop(uid)
        await event.respond(CONSENT, buttons=[[Button.inline("✅ I agree", b"lg:agree"),
                                               Button.inline("✖️ Cancel", b"lg:cancel")]])

    @bot.on(events.NewMessage(pattern=r"(?i)^/login(?:@\w+)?$", func=lambda e: e.is_private))
    async def login_cmd(event):
        await begin(event)

    @bot.on(events.CallbackQuery(pattern=rb"^(lg:|st:login)"))
    async def login_buttons(event):
        uid, data = event.sender_id, event.data.decode()
        if not access.allowed(uid):
            if data.startswith("lg:"):  # st: buttons are already answered by panel.py
                await event.answer("You are not authorized to use this bot.", alert=True)
            return
        if data == "st:login":
            await event.answer()
            await begin(event)
        elif data == "lg:agree":
            flows[uid] = {"step": "phone", "ts": time.time()}
            await event.answer()
            await event.respond("📱 Send your phone number with country code, e.g. `+911234567890`.")
        elif data == "lg:cancel":
            drop(uid)
            await event.answer("Cancelled")
            await event.respond("Login cancelled.")
        elif data == "lg:logout:yes":
            await event.answer()
            await do_logout(event)
        elif data == "lg:logout:no":
            await event.answer("Kept")

    @bot.on(events.NewMessage(pattern=r"(?i)^/logout(?:@\w+)?$", func=lambda e: e.is_private))
    async def logout_cmd(event):
        if event.sender_id not in hosted:
            await event.respond("You don't have a hosted userbot.")
            return
        await event.respond("Remove your userbot and delete your stored sessions?",
                            buttons=[[Button.inline("🗑 Yes, remove", b"lg:logout:yes"),
                                      Button.inline("Keep", b"lg:logout:no")]])

    async def do_logout(event):
        uid = event.sender_id
        ctx = hosted.pop(uid, None)
        if ctx is None:
            await event.respond("Nothing to remove.")
            return
        revoked_second = True
        record = {}
        try:
            record = next((r for i, r in await vault.load_all() if i == uid), {})
        except Exception:
            pass
        for task in list(ctx.tasks):
            task.cancel()
        if record.get("pyro_hash"):
            try:
                from telethon.tl.functions.account import ResetAuthorizationRequest

                await ctx.client(ResetAuthorizationRequest(hash=record["pyro_hash"]))
            except Exception:
                revoked_second = False
        elif record.get("pyro"):
            revoked_second = False
        try:
            await ctx.client.log_out()
        except Exception:
            await _quiet_disconnect(ctx.client)
        try:
            await vault.delete(uid)
        except Exception:
            log.exception("Vault delete failed for %s", uid)
        note = "✅ Your userbot was removed and your stored sessions deleted."
        if not revoked_second:
            note += ("\n⚠️ One extra session may still be listed in Telegram → Settings → Devices. "
                     "Terminate any session you don't recognise there.")
        await event.respond(note)

    @bot.on(events.NewMessage(func=lambda e: e.is_private and e.sender_id in flows))
    async def flow_input(event):
        from telethon.errors import (FloodWaitError, PasswordHashInvalidError, PhoneCodeExpiredError,
                                     PhoneCodeInvalidError, PhoneNumberInvalidError,
                                     SessionPasswordNeededError)

        uid, text = event.sender_id, (event.raw_text or "").strip()
        flow = fresh(uid)
        if flow is None:
            await event.respond("⌛ That login expired. Send /login to start again.")
            return
        if text.startswith("/"):
            return
        flow["ts"] = time.time()
        step = flow["step"]
        try:
            if step == "phone":
                phone = "+" + _digits(text)
                if len(phone) < 8:
                    await event.respond("❌ That doesn't look like a phone number. Include the country code.")
                    return
                client = TelegramClient(StringSession(), cfg.API_ID, cfg.API_HASH)
                await client.connect()
                flow["client"], flow["phone"] = client, phone
                sent = await client.send_code_request(phone)
                flow["hash"], flow["step"] = sent.phone_code_hash, "code"
                await event.respond(
                    "📩 A login code was sent to your Telegram app. Send it **with spaces between the digits** "
                    "(e.g. `1 2 3 4 5`) — Telegram cancels codes sent as plain digits."
                )
            elif step == "code":
                code = _digits(text)
                try:
                    await flow["client"].sign_in(flow["phone"], code, phone_code_hash=flow["hash"])
                except SessionPasswordNeededError:
                    flow["step"] = "password"
                    await event.respond("🔑 Two-step verification is on. Send your 2FA password.")
                    return
                await finish(event, flow)
            elif step == "password":
                try:
                    await event.delete()  # don't leave the password sitting in the chat
                except Exception:
                    pass
                flow["password"] = text
                await flow["client"].sign_in(password=text)
                await finish(event, flow)
        except PhoneNumberInvalidError:
            drop(uid)
            await event.respond("❌ Telegram rejected that phone number. Send /login to try again.")
        except (PhoneCodeInvalidError, PhoneCodeExpiredError):
            await event.respond("❌ Wrong or expired code. Send the code again, or /login to restart.")
        except PasswordHashInvalidError:
            await event.respond("❌ Wrong 2FA password. Try again.")
        except FloodWaitError as exc:
            drop(uid)
            await event.respond(f"⏳ Too many attempts. Try again in {exc.seconds} seconds.")
        except Exception:
            log.exception("Login step %s failed", step)  # never logs the code or password
            drop(uid)
            await event.respond("⚠️ Something went wrong. Send /login to start again.")

    async def finish(event, flow):
        uid = event.sender_id
        client = flow["client"]
        me = await client.get_me()
        tg_string = client.session.save()
        pyro, pyro_hash = await second_session(client, me, flow.get("password"))
        await _quiet_disconnect(client)
        flow.pop("client", None)
        flows.pop(uid, None)

        await vault.save(me.id, {"tg": tg_string, "pyro": pyro, "pyro_hash": pyro_hash, "owner_chat": uid})
        ctx = await start_account(tg_string, len(hosted))
        if ctx is None:
            await vault.delete(me.id)
            await event.respond("❌ Login worked but the userbot could not start. Nothing was stored.")
            return
        ctx.bot = bot
        hosted[me.id] = ctx
        task = asyncio.create_task(ctx.client.run_until_disconnected())
        tasks.add(task)
        task.add_done_callback(tasks.discard)
        await event.respond(
            f"✅ **Userbot hosted!**\n\n👤 {me.first_name or 'You'} (`{me.id}`)\n"
            f"🧬 Sessions: Telethon ✅ · Pyrogram {'✅' if pyro else '⚠️ not created'}\n\n"
            f"Open any chat and send `{cfg.PREFIX}ping`. Browse commands with /help. "
            "Remove everything any time with /logout."
        )
        await announce(me, len(hosted))

    async def announce(me, total):
        if not cfg.HOSTED_LOG_CHAT:
            return
        now = datetime.now(timezone.utc)
        card = (
            "┌── **New Userbot Hosted**\n"
            f"│ 👤 Name: {me.first_name or '—'}\n"
            f"│ 🆔 User ID: `{me.id}`\n"
            f"│ 🤖 Total Hosted: **{total}**\n"
            f"│ 🕒 Time: `{now:%H:%M:%S}` UTC\n"
            f"└ 📅 Date: `{now:%Y-%m-%d}`"
        )
        try:
            target = int(cfg.HOSTED_LOG_CHAT) if cfg.HOSTED_LOG_CHAT.lstrip("-").isdigit() else cfg.HOSTED_LOG_CHAT
            await bot.send_message(target, card)
        except Exception:
            log.warning("Could not post to HOSTED_LOG_CHAT", exc_info=True)


async def restore(start_account, hosted: dict, tasks: set, bot) -> None:
    """Bring every stored hosted userbot back online after a restart."""
    if not vault.enabled():
        return
    for uid, record in await vault.load_all():
        if uid in hosted:
            continue
        try:
            ctx = await start_account(record["tg"], len(hosted))
        except Exception:
            log.exception("Could not restore hosted account %s — will retry on next restart", uid)
            continue
        if ctx is None:  # session revoked by its owner: forget it
            log.info("Hosted account %s no longer authorised — removing from vault", uid)
            await vault.delete(uid)
            continue
        ctx.bot = bot
        hosted[uid] = ctx
        task = asyncio.create_task(ctx.client.run_until_disconnected())
        tasks.add(task)
        task.add_done_callback(tasks.discard)
