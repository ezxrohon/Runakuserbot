import platform
import time

import telethon

from ..branding import BRAND, TAGLINE
from ..context import say
from ..helpers import fmt_duration
from .. import __version__

NAME = "core"
TITLE = "⚙️ Core"
DESC = "Ping, alive, IDs, user info and the help list."
DEFAULT_ON = True
LOCKED = True
COMMANDS = [
    ("ping", "Latency check"),
    ("alive", "Status card"),
    ("id", "Chat / user / message IDs"),
    ("info", "Info about the replied user (or you)"),
    ("help", "Show all enabled commands"),
]


def setup(ctx):
    @ctx.command(NAME, "ping")
    async def ping(event, arg):
        start = time.perf_counter()
        await say(event, "🏓 ...")
        ms = (time.perf_counter() - start) * 1000
        await say(event, f"🏓 **Pong!** `{ms:.0f} ms`")

    @ctx.command(NAME, "alive")
    async def alive(event, arg):
        panel = "connected" if ctx.bot else "not configured"
        on = sum(1 for m in ctx.registry if ctx.is_enabled(m))
        await say(
            event,
            f"**{BRAND}** `v{__version__}`\n_{TAGLINE}_\n\n"
            f"✅ Status: **online**\n"
            f"⏱ Uptime: `{fmt_duration(time.time() - ctx.started)}`\n"
            f"🐍 Python `{platform.python_version()}` · Telethon `{telethon.__version__}`\n"
            f"🧩 Plugins on: **{on}/{len(ctx.registry)}**\n"
            f"🎛 Bot panel: {panel}",
        )

    @ctx.command(NAME, "id")
    async def get_id(event, arg):
        lines = [f"💬 Chat: `{event.chat_id}`", f"👤 You: `{ctx.me.id}`"]
        reply = await event.get_reply_message()
        if reply:
            lines.append(f"↩️ Replied user: `{reply.sender_id}`")
            lines.append(f"✉️ Replied message: `{reply.id}`")
        await say(event, "\n".join(lines))

    @ctx.command(NAME, "info")
    async def info(event, arg):
        reply = await event.get_reply_message()
        user = (await reply.get_sender()) if reply else ctx.me
        name = " ".join(filter(None, [getattr(user, "first_name", None), getattr(user, "last_name", None)])) or "—"
        username = f"@{user.username}" if getattr(user, "username", None) else "none"
        await say(
            event,
            f"👤 **Name:** {name}\n🔗 **Username:** {username}\n"
            f"🆔 **ID:** `{user.id}`\n🤖 **Bot:** {'yes' if getattr(user, 'bot', False) else 'no'}",
        )

    @ctx.command(NAME, "help")
    async def help_cmd(event, arg):
        await say(event, ctx.help_text())
