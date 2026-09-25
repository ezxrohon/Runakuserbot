"""Text styling commands implemented with the shared Runak helpers."""
from ..context import say
from ..helpers import FONTS, small_caps

NAME = "fonts"
TITLE = "🔤 Fonts"
DESC = "Convert text to Unicode font styles."
DEFAULT_ON = True
COMMANDS = [("font <bold|sans|mono|circle|small> <text>", "Style text"), ("smallcaps <text>", "Small caps")]


def setup(ctx):
    @ctx.command(NAME, "font")
    async def font(event, arg):
        style, _, text = arg.partition(" ")
        if style.lower() not in FONTS or not text.strip():
            await say(event, "Usage: `.font <" + "|".join(FONTS) + "> <text>`")
            return
        await say(event, FONTS[style.lower()](text), md=False)

    @ctx.command(NAME, "smallcaps")
    async def smallcaps_cmd(event, arg):
        await say(event, small_caps(arg) if arg else "Usage: `.smallcaps <text>`", md=False)
