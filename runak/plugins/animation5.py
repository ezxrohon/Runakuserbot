"""Native text animations compatible with the shared Runak context."""
import asyncio

from ..context import say

NAME = "animation5"
TITLE = "🎞️ Animations III"
DESC = "Offline loading, reaction and emoji animations."
DEFAULT_ON = True
COMMANDS = [("loading|asquare|up|hart|anim|fnl|monkey|herber|hand|gsg|theart", "Run a text animation")]


async def _animate(event, frames, delay=0.3):
    reply = await event.respond(frames[0], parse_mode=None)
    for frame in frames[1:]:
        await asyncio.sleep(delay)
        try:
            await reply.edit(frame, parse_mode=None)
        except Exception:
            break


def setup(ctx):
    animations = {
        "loading": ["▯", "▮", "▬", "▭", "✅"],
        "asquare": ["◨", "◧", "◨", "◧", "✅"],
        "up": ["╻", "╹", "╻", "╹", "✅"],
        "hart": ["🖤", "❤️", "🖤", "❤️", "💖"],
        "anim": ["😢", "😧", "😡", "😁", "🙂"],
        "fnl": ["😁🏿", "😁🏾", "😁🏽", "😁🏼", "😁"],
        "monkey": ["🐵", "🙉", "🙈", "🙊", "🐵"],
        "herber": ["Powering on…", "CPU: 25%", "CPU: 60%", "CPU: 100%", "✅ Ready"],
        "hand": ["🖐️", "👈", "👉", "☝️", "✌️", "🤞", "👌"],
        "gsg": ["🔟", "9️⃣", "8️⃣", "7️⃣", "6️⃣", "5️⃣", "4️⃣", "3️⃣", "2️⃣", "1️⃣", "0️⃣"],
        "theart": ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "💖"],
    }
    for command, frames in animations.items():
        @ctx.command(NAME, command)
        async def animation(event, arg, frames=frames):
            await _animate(event, frames)
