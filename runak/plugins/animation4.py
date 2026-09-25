"""Native text animations compatible with the shared Runak context."""
import asyncio

from ..context import say

NAME = "animation4"
TITLE = "🎞️ Animations II"
DESC = "Offline text animations from the legacy animation pack."
DEFAULT_ON = True
COMMANDS = [("kilr|eye|uff|hmm|thinking|snake|human|mc|virus|repe|nikal|music|squ", "Run a text animation")]


async def _animate(event, frames, delay=0.35, final=True):
    reply = await event.respond(frames[0], parse_mode=None)
    for frame in frames[1:]:
        await asyncio.sleep(delay)
        try:
            await reply.edit(frame, parse_mode=None)
        except Exception:
            break
    if final:
        return reply


def setup(ctx):
    animations = {
        "kilr": ["Ready…", "🎯", "🎯 💨", "🎯 💨 Done!"],
        "eye": ["👁️", "👁️ 👁️", "👁️ 👁️\n  👄", "👁️ 👁️\n  👀"],
        "uff": ["U", "Uf", "Uff", "Uffff", "Uffff!"],
        "hmm": ["Hm", "Hmm", "Hmmm", "Hmmm…"],
        "thinking": ["Thinking.", "Thinking..", "Thinking...", "💭 Done thinking."],
        "snake": ["🐍", "🐍➰", "🐍➰➰", "🐍➰➰➰"],
        "human": ["🚗", "  🚗", "    🚗", "🙂"],
        "mc": ["◼️◼️◼️◼️◼️", "◼️◼️◼️◼️◻️", "◼️◼️◼️◻️◻️", "✅"],
        "virus": ["Scanning…", "Scanning… 🔴", "Scanning… 🟡", "✅ No virus found."],
        "repe": ["🚂", "🚂🚃", "🚂🚃🚃", "🚂🚃🚃🚃"],
        "nikal": ["🚪", "🚶", "👋", "Gone!"],
        "music": ["▶️ Loading…", "▶️ ♪ ♫", "🎵 ♪ ♫ 🎵", "🎶 Now playing!"],
        "squ": ["▱", "▱▱", "▱▱▱", "▱▱▱▱", "✅"],
    }
    for command, frames in animations.items():
        @ctx.command(NAME, command)
        async def animation(event, arg, frames=frames):
            await _animate(event, frames)
