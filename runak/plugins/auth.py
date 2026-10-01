"""Public authentication help entry point.

`.auth` is intentionally informational for incoming users.
It never asks for, collects, or stores Telegram login codes,
2FA passwords, or StringSessions from arbitrary users.
"""

import re

from telethon import events

from .. import config as cfg
from ..branding import BRAND

NAME = "auth"
TITLE = "🔐 Auth"
DESC = "Public account-auth help without exposing login credentials."
DEFAULT_ON = True
LOCKED = True

COMMANDS = [
    ("auth", "Show safe account-auth instructions"),
]


def setup(ctx):
    @ctx.client.on(
        events.NewMessage(
            incoming=True,
            pattern=rf"(?is)^{re.escape(cfg.PREFIX)}auth(?:\s+(.+))?$",
        )
    )
    async def public_auth(event):
        # Only respond to real users, not bots.
        sender = await event.get_sender()
        if getattr(sender, "bot", False):
            return

        # Only allow the public command in private chats.
        if not event.is_private:
            return

        await event.respond(
            f"**╭━━━ 🔐 {BRAND} AUTH ━━━╮**\n"
            f"**┃** 💎 Public Account Authentication\n"
            f"**╰━━━━━━━━━━━━━━━━━━╯**\n\n"
            "🔐 **Safe account linking**\n\n"
            "• Never send your Telegram login code to anyone.\n"
            "• Never share your 2FA password.\n"
            "• Never post your StringSession publicly.\n"
            "• Additional accounts should be connected through "
            "the owner's account-management panel.\n\n"
            "✨ **Multi-account support:**\n"
            "You can connect additional Telegram accounts that "
            "you own using the project's account-management system.\n\n"
            "🛡️ Your authentication credentials should remain private."
        )
