"""Native offline emoji text-art plugin."""
from ..context import say

NAME = "emojify"
TITLE = "😀 Emojify"
DESC = "Render text using compact emoji letter art."
DEFAULT_ON = True
COMMANDS = [("emoji <text>", "Render text as emoji art"), ("cmoji <emoji> <text>", "Render text with a chosen emoji")]

_BLOCK = {
    "a": "🅰️", "b": "🅱️", "c": "©️", "i": "ℹ️", "m": "Ⓜ️",
    "o": "🅾️", "p": "🅿️", "r": "®️", "x": "❌", "!": "❗",
    "?": "❓", "0": "0️⃣", "1": "1️⃣", "2": "2️⃣", "3": "3️⃣",
    "4": "4️⃣", "5": "5️⃣", "6": "6️⃣", "7": "7️⃣", "8": "8️⃣", "9": "9️⃣",
}


def _render(text, emoji=None):
    if emoji:
        return " ".join(emoji if ch != " " else "   " for ch in text)
    return " ".join(_BLOCK.get(ch.lower(), ch) for ch in text)


def setup(ctx):
    @ctx.command(NAME, "emoji")
    async def emoji(event, arg):
        text = arg.strip()
        if not text:
            reply = await event.get_reply_message()
            text = (reply.raw_text or "").strip() if reply else ""
        await say(event, _render(text) if text else "Usage: `.emoji <text>`", md=False)

    @ctx.command(NAME, "cmoji")
    async def cmoji(event, arg):
        icon, _, text = arg.partition(" ")
        if not text:
            await say(event, "Usage: `.cmoji <emoji> <text>`", md=False)
            return
        await say(event, _render(text, icon[:2]), md=False)
