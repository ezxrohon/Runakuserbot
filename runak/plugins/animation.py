"""Native animation commands compatible with the shared Runak context."""
import asyncio
import random
import time

from ..context import say

NAME = "animation"
TITLE = "🎞️ Advanced Animations"
DESC = "Typing, spinner, matrix, hearts and countdown effects."
DEFAULT_ON = True
CATEGORY = "animations"
COMMANDS = [
    ("animate", "Type out a message one character at a time"),
    ("spinner", "Show a spinner animation"),
    ("loveu", "Rainbow heart animation"),
    ("matrix", "Show a matrix rain animation"),
    ("hearts", "Wrap text in heart bubbles"),
    ("countdown", "Count down from N to zero"),
    ("wave", "Animate a text wave"),
]


def _safe_edit(msg, text):
    try:
        return msg.edit(text)
    except Exception:
        return None


def setup(ctx):
    @ctx.command(NAME, "animate")
    async def animate(event, arg):
        text = (arg or "").strip()
        if not text:
            await say(event, "Usage: `.animate <text>`", md=False)
            return
        msg = await event.respond("⏳")
        for i in range(1, len(text) + 1):
            await _safe_edit(msg, text[:i])
            await asyncio.sleep(0.05 + random.random() * 0.1)
        await asyncio.sleep(0.5)

    @ctx.command(NAME, "spinner")
    async def spinner(event, arg):
        frames = ["|", "/", "—", "\\"]
        seconds = int(arg) if arg and arg.isdigit() else 5
        msg = await event.respond("⏳ Starting spinner…")
        start = time.monotonic()
        idx = 0
        while time.monotonic() - start < seconds:
            frame = frames[idx % len(frames)]
            await _safe_edit(msg, f"{frame} spinning…")
            idx += 1
            await asyncio.sleep(0.2)
        await _safe_edit(msg, "✅ Done!")

    @ctx.command(NAME, "loveu")
    async def loveu(event, arg):
        hearts = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "💖", "💗", "💓"]
        msg = await event.respond("💞")
        for i in range(len(hearts) * 3):
            await _safe_edit(msg, hearts[i % len(hearts)])
            await asyncio.sleep(0.3)
        await _safe_edit(msg, "I ❤️ U")

    @ctx.command(NAME, "matrix")
    async def matrix(event, arg):
        seconds = int(arg) if arg and arg.isdigit() else 5
        msg = await event.respond("Loading Matrix…")
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            lines = []
            for _ in range(6):
                line = "".join(random.choice(["0", "1", " "]) for _ in range(20))
                lines.append(line)
            await _safe_edit(msg, f"```{'\n'.join(lines)}```")
            await asyncio.sleep(0.5)
        await _safe_edit(msg, "🔚 Matrix end")

    @ctx.command(NAME, "hearts")
    async def hearts(event, arg):
        text = (arg or "").strip()
        if not text:
            await say(event, "Usage: `.hearts <text>`", md=False)
            return
        msg = await event.respond(f"💖 {text} 💖")
        frames = [
            f"💘 {text} 💘",
            f"💕 {text} 💕",
            f"💞 {text} 💞",
            f"💓 {text} 💓",
        ]
        for i in range(len(frames) * 2):
            await _safe_edit(msg, frames[i % len(frames)])
            await asyncio.sleep(0.6)
        await _safe_edit(msg, f"💖 {text} 💖")

    @ctx.command(NAME, "countdown")
    async def countdown(event, arg):
        if not arg or not arg.isdigit():
            await say(event, "Usage: `.countdown <n>`", md=False)
            return
        start = int(arg)
        msg = await event.respond(str(start))
        for n in range(start - 1, -1, -1):
            await asyncio.sleep(1)
            await _safe_edit(msg, str(n))
        await asyncio.sleep(0.5)
        await _safe_edit(msg, "🎉 Boom!")

    @ctx.command(NAME, "wave")
    async def wave(event, arg):
        text = (arg or "").strip()
        if not text:
            await say(event, "Usage: `.wave <text>`", md=False)
            return
        msg = await event.respond(text)
        width = len(text) + 4
        pos = 0
        direction = 1
        for _ in range(width * 2):
            await _safe_edit(msg, (" " * pos) + text)
            if pos == width or pos == 0:
                direction *= -1
            pos += direction
            await asyncio.sleep(0.1)
        await _safe_edit(msg, text)
