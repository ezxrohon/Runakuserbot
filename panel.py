"""Control panel: a normal Telegram bot (from @BotFather) that only YOU can use.

Send /start to your bot to open it. Everything is inline buttons.
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


def setup(ctx):
    bot = ctx.bot
    owner = ctx.me.id
    awaiting = {}  # what free-text input we are waiting for from the owner

    def onoff(flag: bool) -> str:
        return "✅ ON" if flag else "❌ OFF"

    # ── views: each returns (text, buttons) ───────────────────────────
    def home():
        text = f"**{BRAND}**\n_{TAGLINE}_\n\nChoose a section:"
        return text, [
            [Button.inline("📊 Status", b"status"), Button.inline("🧩 Plugins", b"plugins")],
            [Button.inline("🤖 AI Reply", b"ai"), Button.inline("🌙 AFK", b"afk")],
            [Button.inline("⏰ Reminders", b"reminders"), Button.inline("📖 Commands", b"commands")],
            [Button.inline("ℹ️ About", b"about"), Button.inline("♻️ Restart", b"restart")],
        ]

    def status():
        on = sum(1 for m in ctx.registry if ctx.is_enabled(m))
        afk = ctx.store.data["afk"]
        name = ctx.me.first_name or "You"
        text = (
            f"**{BRAND} — Status**\n\n"
            f"👤 {name} (`{ctx.me.id}`)\n"
            f"⏱ Uptime: `{fmt_duration(time.time() - ctx.started)}`\n"
            f"🐍 Python `{platform.python_version()}`\n"
            f"🧩 Plugins on: **{on}/{len(ctx.registry)}**\n"
            f"🤖 AI: {onoff(ctx.enabled('ai'))}\n"
            f"🌙 AFK: {onoff(afk['on'])}\n"
            f"📝 Notes: **{len(ctx.store.data['notes'])}** · ⏰ Reminders: **{len(ctx.store.data['reminders'])}**\n"
            f"💾 Settings: `{ctx.store.size()}` / 3800 chars used"
        )
        return text, [[Button.inline("⬅️ Back", b"home")]]

    def plugins():
        rows = []
        for m in ctx.registry:
            if getattr(m, "LOCKED", False):
                rows.append([Button.inline(f"🔒 {m.TITLE} (always on)", b"noop")])
            else:
                mark = "✅" if ctx.is_enabled(m) else "❌"
                rows.append([Button.inline(f"{mark} {m.TITLE}", f"tg:{m.NAME}".encode())])
        rows.append([Button.inline("⬅️ Back", b"home")])
        return "**🧩 Plugins**\nTap to switch a plugin on or off.", rows

    def ai():
        warn = "" if cfg.GROQ_API_KEY else "\n⚠️ `GROQ_API_KEY` is not set."
        scope = ctx.store.data["ai"].get("scope", "contacts")
        text = (
            f"**🤖 AI Auto-Reply** — {onoff(ctx.enabled('ai'))}\n"
            f"Model: `{cfg.GROQ_MODEL}`\nReplies in private chats only.{warn}\n"
            f"Who gets replies: **{'saved contacts only' if scope == 'contacts' else 'everyone'}**\n\n"
            f"Personality:\n`{(ctx.store.data['ai'].get('prompt') or cfg.DEFAULT_PROMPT)[:300]}`"
        )
        return text, [
            [Button.inline("Switch ON/OFF", b"tg:ai")],
            [Button.inline("👥 Contacts only ⇄ Everyone", b"ai:scope")],
            [Button.inline("✏️ Set personality", b"ask:prompt"), Button.inline("↩️ Reset", b"ai:reset")],
            [Button.inline("⬅️ Back", b"home")],
        ]

    def afk():
        a = ctx.store.data["afk"]
        text = f"**🌙 AFK** — {onoff(a['on'])}\nReason: {a['reason'] or '—'}"
        return text, [
            [Button.inline("Switch ON/OFF", b"afk:toggle")],
            [Button.inline("✏️ Set reason", b"ask:afk")],
            [Button.inline("⬅️ Back", b"home")],
        ]

    def reminders():
        from .plugins.remind import local_time

        items = ctx.store.data["reminders"]
        lines = [f"`{i}.` {local_time(r['due'])} — {r['text']}" for i, r in enumerate(items, 1)]
        text = "**⏰ Reminders**\n" + ("\n".join(lines) if lines else "None pending.")
        rows = [[Button.inline("🗑 Clear all", b"rem:clear")]] if items else []
        rows.append([Button.inline("⬅️ Back", b"home")])
        return text, rows

    def commands():
        return ctx.help_text(), [[Button.inline("⬅️ Back", b"home")]]

    def about():
        text = (
            f"**{BRAND}** `v{__version__}`\n_{TAGLINE}_\n\n"
            "🔒 Only your own account can run commands, and only you can use this panel.\n"
            "🧱 No remote plugin installer, no auto-updater, no hidden admins.\n"
            "🙈 Secrets are never logged or sent anywhere.\n\n"
            f"Powered by {BRAND}"
        )
        return text, [[Button.inline("⬅️ Back", b"home")]]

    def restart():
        return "♻️ Restart the userbot now?", [
            [Button.inline("Yes, restart", b"restart:yes"), Button.inline("Cancel", b"home")]
        ]

    views = {
        "home": home, "status": status, "plugins": plugins, "ai": ai, "afk": afk,
        "reminders": reminders, "commands": commands, "about": about, "restart": restart,
    }

    async def show(event, key):
        text, buttons = views[key]()
        try:
            await event.edit(text, buttons=buttons)
        except Exception:  # e.g. "message not modified"
            pass

    # ── handlers ──────────────────────────────────────────────────────
    @bot.on(events.NewMessage(pattern=r"(?i)^/(start|panel|menu)(?:@\w+)?$", func=lambda e: e.is_private))
    async def start(event):
        if event.sender_id != owner:
            await event.respond(f"**{BRAND}**\nThis panel is private.")
            return
        awaiting.pop(owner, None)
        text, buttons = home()
        await event.respond(text, buttons=buttons)

    @bot.on(events.CallbackQuery())
    async def callbacks(event):
        if event.sender_id != owner:
            await event.answer("This panel is private.", alert=True)
            return
        data = event.data.decode()

        if data == "noop":
            await event.answer("Core can't be switched off.")
            return
        if data.startswith("tg:"):
            name = data[3:]
            module = next((m for m in ctx.registry if m.NAME == name), None)
            if module and not getattr(module, "LOCKED", False):
                if name == "ai" and not ctx.enabled("ai") and not cfg.GROQ_API_KEY:
                    await event.answer("Set GROQ_API_KEY first.", alert=True)
                    return
                ctx.set_enabled(name, not ctx.is_enabled(module))
            await event.answer("Updated")
            await show(event, "ai" if name == "ai" else "plugins")
            return
        if data == "afk:toggle":
            a = ctx.store.data["afk"]
            a["on"] = not a["on"]
            if a["on"]:
                a["since"] = int(time.time())
                a["reason"] = a["reason"] or "I'm away right now. I'll reply when I'm back."
            ctx.afk_notified.clear()
            ctx.store.save_soon()
            await event.answer("Updated")
            await show(event, "afk")
            return
        if data == "ai:scope":
            ai_data = ctx.store.data["ai"]
            ai_data["scope"] = "everyone" if ai_data.get("scope", "contacts") == "contacts" else "contacts"
            ctx.store.save_soon()
            await event.answer("Updated")
            await show(event, "ai")
            return
        if data == "ai:reset":
            ctx.store.data["ai"]["prompt"] = None
            ctx.store.save_soon()
            await event.answer("Personality reset")
            await show(event, "ai")
            return
        if data == "rem:clear":
            ctx.store.data["reminders"].clear()
            ctx.store.save_soon()
            await event.answer("Cleared")
            await show(event, "reminders")
            return
        if data.startswith("ask:"):
            awaiting[owner] = data[4:]
            await event.answer()
            hint = "the new AI personality" if data == "ask:prompt" else "your AFK reason"
            await event.respond(f"✏️ Send {hint} as your next message.")
            return
        if data == "restart:yes":
            await event.answer("Restarting…")
            await event.edit("♻️ Restarting… back in a few seconds.")
            log.warning("Restart requested from panel")
            await ctx.store.flush()
            await ctx.client.disconnect()
            os._exit(0)  # the host (Render) starts a fresh process
        if data in views:
            await event.answer()
            await show(event, data)

    @bot.on(events.NewMessage(func=lambda e: e.is_private and e.sender_id == owner))
    async def free_text(event):
        field = awaiting.get(owner)
        text = (event.raw_text or "").strip()
        if not field or not text or text.startswith("/"):
            return
        awaiting.pop(owner, None)
        if field == "prompt":
            ctx.store.data["ai"]["prompt"] = text[:1500]
            note = "✅ AI personality updated."
        else:
            ctx.store.data["afk"]["reason"] = text[:300]
            note = "✅ AFK reason updated."
        ctx.store.save_soon()
        await event.respond(note, buttons=[[Button.inline("⬅️ Panel", b"home")]])
