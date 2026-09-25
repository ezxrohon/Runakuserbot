"""Generate display-name variants without external userbot dependencies."""
from ..context import say
from ..helpers import FONTS, small_caps

NAME = "namestyle"
TITLE = "✨ Name Styles"
DESC = "Generate safe Unicode display-name variants."
DEFAULT_ON = True
COMMANDS = [("namestyle <name>", "Generate name variants")]


def setup(ctx):
    @ctx.command(NAME, "namestyle")
    async def namestyle(event, arg):
        text = " ".join(arg.split())
        if not text:
            reply = await event.get_reply_message()
            text = (reply.raw_text or "").strip() if reply else ""
        if not text:
            await say(event, "Usage: `.namestyle <name>`", md=False)
            return
        if len(text) > 40:
            await say(event, "❌ Keep the name under 40 characters.", md=False)
            return
        variants = [FONTS[style](text) for style in ("bold", "sans", "mono", "circle")]
        variants += [small_caps(text), "𓆩『✦ " + text + " ✦』𓆪"]
        await say(event, "✨ **Name styles**\n\n" + "\n".join(f"`{v}`" for v in variants))
