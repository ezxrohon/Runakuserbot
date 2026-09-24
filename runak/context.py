"""Shared context handed to every plugin and to the control panel."""
import logging
import re
import time

from telethon import events
from telethon.tl.types import User

from . import config as cfg
from .branding import BRAND

log = logging.getLogger("runak")


async def say(event, text: str, md: bool = True):
    """Edit the command message in place (fall back to a new message)."""
    kwargs = {} if md else {"parse_mode": None}
    try:
        await event.edit(text, **kwargs)
    except Exception:
        await event.respond(text, **kwargs)


class Ctx:
    def __init__(self, client, store, me):
        self.client = client
        self.store = store
        self.me = me
        self.bot = None
        self.started = time.time()
        self.registry = []          # loaded plugin modules
        self.afk_notified = set()   # who already got the AFK notice
        self.tasks = []             # background tasks owned by plugins

    # ── plugin switches ────────────────────────────────────────────────
    def is_enabled(self, module) -> bool:
        if getattr(module, "LOCKED", False):
            return True
        return bool(self.store.data["plugins"].get(module.NAME, module.DEFAULT_ON))

    def enabled(self, name: str) -> bool:
        return any(self.is_enabled(m) for m in self.registry if m.NAME == name)

    def set_enabled(self, name: str, value: bool):
        self.store.data["plugins"][name] = bool(value)
        self.store.save_soon()

    # ── handler helpers ────────────────────────────────────────────────
    def command(self, plugin: str, *names: str, always: bool = False):
        """Register an owner-only command.

        Only *outgoing* messages (sent by your own account) can trigger it,
        so nobody else can ever run your commands.
        """
        alt = "|".join(re.escape(n) for n in names)
        pattern = rf"(?is)^{re.escape(cfg.PREFIX)}(?:{alt})(?:\s+(.+))?$"

        def deco(fn):
            @self.client.on(events.NewMessage(outgoing=True, pattern=pattern))
            async def wrapper(event):
                if not always and not self.enabled(plugin):
                    return
                try:
                    await fn(event, (event.pattern_match.group(1) or "").strip())
                except Exception:
                    log.exception("Command %s failed", names[0])
                    try:
                        await event.edit("⚠️ Something went wrong. Check the logs.")
                    except Exception:
                        pass

            return wrapper

        return deco

    def on_dm(self, plugin: str):
        """Register a handler for incoming private messages."""

        def deco(fn):
            @self.client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
            async def wrapper(event):
                if not self.enabled(plugin):
                    return
                if event.sender_id in (None, self.me.id, 777000):
                    return
                try:
                    await fn(event)
                except Exception:
                    log.exception("DM handler for %s failed", plugin)

            return wrapper

        return deco

    async def human_sender(self, event):
        sender = await event.get_sender()
        if isinstance(sender, User) and not sender.bot and not sender.deleted and sender.id != self.me.id:
            return sender
        return None

    def help_text(self) -> str:
        """Markdown list of every plugin's commands (plugins that are off are hidden)."""
        out = [f"**{BRAND} — Commands**", ""]
        for module in self.registry:
            if not self.is_enabled(module) and not getattr(module, "TOGGLE", False):
                continue
            state = "" if self.is_enabled(module) else " _(off)_"
            out.append(f"**{module.TITLE}**{state}")
            for usage, desc in module.COMMANDS:
                out.append(f"`{cfg.PREFIX}{usage}` — {desc}")
            out.append("")
        text = "\n".join(out).strip()
        return text if len(text) <= 4000 else text[:3990] + "…"
