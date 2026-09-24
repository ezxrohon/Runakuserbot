import base64
import binascii
import random
import secrets
import string
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .. import config as cfg
from ..context import say
from ..helpers import FONTS, calculate, small_caps

NAME = "tools"
TITLE = "🧰 Tools & Fun"
DESC = "Safe calculator, text tools and tiny games."
DEFAULT_ON = True
COMMANDS = [
    ("calc <expr>", "Basic arithmetic (no eval)"),
    ("upper / lower / reverse <text>", "Text transforms"),
    ("small <text>", "ꜱᴍᴀʟʟ ᴄᴀᴘs style"),
    ("b64 / unb64 <text>", "Base64 encode / decode"),
    ("font <bold|sans|mono|circle|small> <text>", "Fancy text styles"),
    ("pass [length]", "Random password (8-64 chars)"),
    ("time [Area/City]", "Current time (e.g. .time Asia/Tokyo)"),
    ("dice · flip · 8ball", "Tiny games"),
]


def setup(ctx):
    async def text_arg(event, arg):
        if arg:
            return arg
        reply = await event.get_reply_message()
        return (reply.raw_text or "") if reply else ""

    @ctx.command(NAME, "calc")
    async def calc(event, arg):
        if not arg:
            await say(event, "Usage: `.calc 12 * (3 + 2)`")
            return
        try:
            await say(event, f"🧮 `{arg}` = **{calculate(arg)}**")
        except Exception:
            await say(event, "❌ Only basic arithmetic is supported.")

    @ctx.command(NAME, "upper")
    async def upper(event, arg):
        text = await text_arg(event, arg)
        await say(event, text.upper() if text else "Usage: .upper <text>", md=False)

    @ctx.command(NAME, "lower")
    async def lower(event, arg):
        text = await text_arg(event, arg)
        await say(event, text.lower() if text else "Usage: .lower <text>", md=False)

    @ctx.command(NAME, "reverse")
    async def reverse(event, arg):
        text = await text_arg(event, arg)
        await say(event, text[::-1] if text else "Usage: .reverse <text>", md=False)

    @ctx.command(NAME, "small")
    async def small(event, arg):
        text = await text_arg(event, arg)
        await say(event, small_caps(text) if text else "Usage: .small <text>", md=False)

    @ctx.command(NAME, "b64")
    async def b64(event, arg):
        text = await text_arg(event, arg)
        out = base64.b64encode(text.encode()).decode() if text else "Usage: .b64 <text>"
        await say(event, out, md=False)

    @ctx.command(NAME, "unb64")
    async def unb64(event, arg):
        text = await text_arg(event, arg)
        try:
            out = base64.b64decode(text, validate=True).decode()
        except (binascii.Error, UnicodeDecodeError, ValueError):
            out = "❌ Not valid base64 text."
        await say(event, out, md=False)

    @ctx.command(NAME, "font")
    async def font(event, arg):
        style, _, rest = arg.partition(" ")
        style = style.lower()
        if style not in FONTS:
            await say(event, "Usage: `.font <" + "|".join(FONTS) + "> <text>`")
            return
        text = await text_arg(event, rest.strip())
        await say(event, FONTS[style](text) if text else "Give me some text.", md=False)

    @ctx.command(NAME, "pass")
    async def password(event, arg):
        length = int(arg) if arg.isdigit() else 16
        length = max(8, min(64, length))
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*-_"
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        await say(event, f"🔑 `{pwd}`\n_Delete this message after copying it._")

    @ctx.command(NAME, "time")
    async def clock(event, arg):
        try:
            zone = ZoneInfo(arg.strip() or cfg.TIMEZONE)
        except (ZoneInfoNotFoundError, ValueError):
            await say(event, "❌ Unknown time zone. Example: `.time Asia/Tokyo`")
            return
        await say(event, f"🕒 `{datetime.now(zone):%Y-%m-%d %H:%M:%S %Z}` — {zone.key}")

    @ctx.command(NAME, "dice")
    async def dice(event, arg):
        await say(event, f"🎲 **{random.randint(1, 6)}**")

    @ctx.command(NAME, "flip")
    async def flip(event, arg):
        await say(event, f"🪙 **{random.choice(['Heads', 'Tails'])}**")

    @ctx.command(NAME, "8ball")
    async def eight_ball(event, arg):
        answers = ["Yes.", "No.", "Probably.", "Ask again later.", "It looks promising.", "Unlikely."]
        await say(event, f"🎱 {random.choice(answers)}")
