"""Control panel: a normal Telegram bot (from @BotFather) that only YOU can use.

Send /start to your bot to open it. Everything is inline buttons. Works the same whether
you're running one account or several — with several, /start opens an account switcher first.
"""
import logging
import os
import platform
import time

from telethon import Button, events

from . import __version__
from . import config as cfg
from .branding import BRAND, TAGLINE
from .helpers import fmt_duration

log = logging.getLogger("runak.panel")


def setup(bot, ctxs: list, add_account=None):
    owner_ids = {c.me.id for c in ctxs}
    if cfg.OWNER_ID:
        owner_ids.add(cfg.OWNER_ID)
    awaiting = {}  # owner_id -> (account_index, field)

    def onoff(flag: bool) -> str:
        return "✅ ON" if flag else "❌ OFF"

    def account_label(ctx) -> str:
        name = ctx.me.first_name or str(ctx.me.id)
        return f"@{ctx.me.username}" if ctx.me.username else name

    def accounts_view():
        text = f"**{BRAND}**\n_{TAGLINE}_\n\n{len(ctxs)} accounts connected. Choose one:"
        rows = [[Button.inline(f"👤 {account_label(c)}", f"a:{i}:home".encode())] for i, c in enumerate(ctxs)]
        if add_account is not None:
            rows.append([Button.inline("➕ Add account", b"account:add")])
        return text, rows

    def home(ctx, i):
        text = f"**{BRAND}**\n_{TAGLINE}_\n👤 {account_label(ctx)}\n\nChoose a section:"
        rows = [
            [Button.inline("📊 Status", f"a:{i}:status".encode()), Button.inline("🧩 Plugins", f"a:{i}:plugins".encode())],
            [Button.inline("🤖 AI Reply", f"a:{i}:ai".encode()), Button.inline("🌙 AFK", f"a:{i}:afk".encode())],
            [Button.inline("⏰ Reminders", f"a:{i}:reminders".encode()), Button.inline("📖 Commands", f"a:{i}:commands".encode())],
            [Button.inline("ℹ️ About", f"a:{i}:about".encode()), Button.inline("♻️ Restart", f"a:{i}:restart".encode())],
        ]
        if len(ctxs) > 1:
            rows.append([Button.inline("🔀 Switch account", b"accounts")])
        return text, rows

    def status(ctx, i):
        on = sum(1 for m in ctx.registry if ctx.is_enabled(m))
        afk = ctx.store.data["afk"]
        text = (
            f"**{BRAND} — Status**\n\n"
            f"👤 {ctx.me.first_name or 'You'} (`{ctx.me.id}`)\n"
            f"⏱ Uptime: `{fmt_duration(time.time() - ctx.started)}`\n"
            f"🐍 Python `{platform.python_version()}`\n"
            f"🧩 Plugins on: **{on}/{len(ctx.registry)}**\n"
            f"🤖 AI: {onoff(ctx.enabled('ai'))}\n"
            f"🌙 AFK: {onoff(afk['on'])}\n"
            f"📝 Notes: **{len(ctx.store.data['notes'])}** · ⏰ Reminders: **{len(ctx.store.data['reminders'])}**\n"
            f"💾 Storage: {'Firestore' if ctx.store._doc is not None else 'Saved Messages'}"
        )
        return text, [[Button.inline("⬅️ Back", f"a:{i}:home".encode())]]

    def plugins(ctx, i):
        rows = []
        for m in ctx.registry:
            if getattr(m, "LOCKED", False):
                rows.append([Button.inline(f"🔒 {m.TITLE} (always on)", b"noop")])
            else:
                mark = "✅" if ctx.is_enabled(m) else "❌"
                rows.append([Button.inline(f"{mark} {m.TITLE}", f"a:{i}:tg:{m.NAME}".encode())])
        rows.append([Button.inline("⬅️ Back", f"a:{i}:home".encode())])
        return "**🧩 Plugins**\nTap to switch a plugin on or off.", rows

    def ai(ctx, i):
        warn = "" if cfg.GROQ_API_KEY else "\n⚠️ `GROQ_API_KEY` is not set."
        data = ctx.store.data["ai"]
        scope = data.get("scope", "contacts")
        small = bool(data.get("smallcaps", True))
        text = (
            f"**🤖 AI Auto-Reply** — {onoff(ctx.enabled('ai'))}\n"
            f"Model: `{cfg.GROQ_MODEL}`\nReplies in private chats only.{warn}\n"
            f"Who gets replies: **{'saved contacts only' if scope == 'contacts' else 'everyone'}**\n"
            f"ꜱᴍᴀʟʟ ᴄᴀᴘꜱ: **{'ON' if small else 'OFF'}**\n\n"
            f"Personality:\n`{(data.get('prompt') or cfg.DEFAULT_PROMPT)[:300]}`"
        )
        return text, [
            [Button.inline("Switch ON/OFF", f"a:{i}:tg:ai".encode())],
            [Button.inline("👥 Contacts only ⇄ Everyone", f"a:{i}:ai:scope".encode())],
            [Button.inline("🔡 Small caps ⇄", f"a:{i}:ai:smallcaps".encode())],
            [Button.inline("✏️ Set personality", f"a:{i}:ask:prompt".encode()), Button.inline("↩️ Reset", f"a:{i}:ai:reset".encode())],
            [Button.inline("⬅️ Back", f"a:{i}:home".encode())],
        ]

    def afk(ctx, i):
        a = ctx.store.data["afk"]
        text = f"**🌙 AFK** — {onoff(a['on'])}\nReason: {a['reason'] or '—'}"
        return text, [
            [Button.inline("Switch ON/OFF", f"a:{i}:afk:toggle".encode())],
            [Button.inline("✏️ Set reason", f"a:{i}:ask:afk".encode())],
            [Button.inline("⬅️ Back", f"a:{i}:home".encode())],
        ]

    def reminders(ctx, i):
        from .plugins.remind import local_time
        items = ctx.store.data["reminders"]
        lines = [f"`{n}.` {local_time(r['due'])} — {r['text']}" for n, r in enumerate(items, 1)]
        text = "**⏰ Reminders**\n" + ("\n".join(lines) if lines else "None pending.")
        rows = [[Button.inline("🗑 Clear all", f"a:{i}:rem:clear".encode())]] if items else []
        rows.append([Button.inline("⬅️ Back", f"a:{i}:home".encode())])
        return text, rows

    def commands(ctx, i):
        return ctx.help_text(), [[Button.inline("⬅️ Back", f"a:{i}:home".encode())]]

    def about(ctx, i):
        text = (
            f"**{BRAND}** `v{__version__}`\n_{TAGLINE}_\n\n"
            "🔒 Only your own account(s) can run commands, and only you can use this panel.\n"
            "🧱 No remote plugin installer, no auto-updater, no hidden admins.\n"
            "🙈 Secrets are never logged or sent anywhere.\n\n"
            f"Powered by {BRAND}"
        )
        return text, [[Button.inline("⬅️ Back", f"a:{i}:home".encode())]]

    def restart(ctx, i):
        return "♻️ Restart the userbot now? This restarts **every connected account**.", [
            [Button.inline("Yes, restart", b"restart:yes"), Button.inline("Cancel", f"a:{i}:home".encode())]
        ]

    views = {"home": home, "status": status, "plugins": plugins, "ai": ai, "afk": afk,
             "reminders": reminders, "commands": commands, "about": about, "restart": restart}

    async def show(event, ctx, i, key):
        text, buttons = views[key](ctx, i)
        try:
            await event.edit(text, buttons=buttons)
        except Exception:
            pass

    async def show_accounts(event):
        text, buttons = accounts_view()
        try:
            await event.edit(text, buttons=buttons)
        except Exception:
            pass

    @bot.on(events.NewMessage(pattern=r"(?i)^/(start|panel|menu)(?:@\w+)?$", func=lambda e: e.is_private))
    async def start(event):
        if event.sender_id not in owner_ids:
            await event.respond(f"**{BRAND}**\nThis panel is private.")
            return
        awaiting.pop(event.sender_id, None)
        text, buttons = home(ctxs[0], 0) if len(ctxs) == 1 else accounts_view()
        await event.respond(text, buttons=buttons)

    @bot.on(events.CallbackQuery())
    async def callbacks(event):
        if event.sender_id not in owner_ids:
            await event.answer("This panel is private.", alert=True)
            return
        data = event.data.decode()
        if data == "noop":
            await event.answer("Core can't be switched off.")
            return
        if data == "accounts":
            await event.answer()
            await show_accounts(event)
            return
        if data == "account:add" and add_account is not None:
            awaiting[event.sender_id] = (0, "session")
            await event.answer()
            await event.respond("🔐 Send the StringSession for your own Telegram account as your next message. It will be used only to connect this process; never share it with anyone else.")
            return
        if data == "restart:yes":
            await event.answer("Restarting…")
            await event.edit("♻️ Restarting… back in a few seconds.")
            log.warning("Restart requested from panel")
            for ctx in ctxs:
                await ctx.store.flush()
                await ctx.client.disconnect()
            os._exit(0)
        if not data.startswith("a:"):
            return
        _, idx_str, action = data.split(":", 2)
        i = int(idx_str)
        if i >= len(ctxs):
            await event.answer("That account is no longer connected.", alert=True)
            return
        ctx = ctxs[i]
        if action == "tg:ai" and not ctx.enabled("ai") and not cfg.GROQ_API_KEY:
            await event.answer("Set GROQ_API_KEY first.", alert=True)
            return
        if action.startswith("tg:"):
            name = action[3:]
            module = next((m for m in ctx.registry if m.NAME == name), None)
            if module and not getattr(module, "LOCKED", False):
                ctx.set_enabled(name, not ctx.is_enabled(module))
            await event.answer("Updated")
            await show(event, ctx, i, "ai" if name == "ai" else "plugins")
            return
        if action == "afk:toggle":
            a = ctx.store.data["afk"]
            a["on"] = not a["on"]
            if a["on"]:
                a["since"] = int(time.time())
                a["reason"] = a["reason"] or "I'm away right now. I'll reply when I'm back."
            ctx.afk_notified.clear()
            ctx.store.save_soon()
            await event.answer("Updated")
            await show(event, ctx, i, "afk")
            return
        if action == "ai:scope":
            data = ctx.store.data["ai"]
            data["scope"] = "everyone" if data.get("scope", "contacts") == "contacts" else "contacts"
            ctx.store.save_soon()
            await event.answer("Updated")
            await show(event, ctx, i, "ai")
            return
        if action == "ai:smallcaps":
            data = ctx.store.data["ai"]
            data["smallcaps"] = not data.get("smallcaps", True)
            ctx.store.save_soon()
            await event.answer("Updated")
            await show(event, ctx, i, "ai")
            return
        if action == "ai:reset":
            ctx.store.data["ai"]["prompt"] = None
            ctx.store.save_soon()
            await event.answer("Personality reset")
            await show(event, ctx, i, "ai")
            return
        if action == "rem:clear":
            ctx.store.data["reminders"].clear()
            ctx.store.save_soon()
            await event.answer("Cleared")
            await show(event, ctx, i, "reminders")
            return
        if action.startswith("ask:"):
            awaiting[event.sender_id] = (i, action[4:])
            await event.answer()
            hint = "the new AI personality" if action == "ask:prompt" else "your AFK reason"
            await event.respond(f"✏️ Send {hint} as your next message.")
            return
        if action in views:
            await event.answer()
            await show(event, ctx, i, action)

    @bot.on(events.NewMessage(func=lambda e: e.is_private and e.sender_id in owner_ids))
    async def free_text(event):
        pending = awaiting.get(event.sender_id)
        text = (event.raw_text or "").strip()
        if not pending or not text or text.startswith("/"):
            return
        i, field = pending
        awaiting.pop(event.sender_id, None)
        if field == "session":
            if len(text) > 500 or any(ch.isspace() for ch in text) or "," in text:
                await event.respond("❌ That does not look like a valid StringSession. Nothing was connected.")
                return
            try:
                new_ctx = await add_account(text)
            except Exception:
                log.exception("Panel account addition failed")
                new_ctx = None
            if new_ctx is None:
                await event.respond("❌ Could not connect that session. Verify it belongs to your account and is authorized.")
            else:
                await event.respond(f"✅ Account **{account_label(new_ctx)}** connected.", buttons=[[Button.inline("👥 Accounts", b"accounts")]])
            return
        ctx = ctxs[i]
        if field == "prompt":
            ctx.store.data["ai"]["prompt"] = text[:1500]
            note = "✅ AI personality updated."
        else:
            ctx.store.data["afk"]["reason"] = text[:300]
            note = "✅ AFK reason updated."
        ctx.store.save_soon()
        await event.respond(note, buttons=[[Button.inline("⬅️ Panel", f"a:{i}:home".encode())]])
