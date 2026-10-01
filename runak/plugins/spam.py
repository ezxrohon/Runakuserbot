"""Safe replacement for the old mass-message spam plugin."""
from ..context import say

NAME = "spam"
TITLE = "🛡 Spam Protection"
DESC = "Mass messaging is disabled; use normal Telegram messages instead."
DEFAULT_ON = False
COMMANDS = [("spam", "Explain why mass messaging is disabled")]


def setup(ctx):
    @ctx.command(NAME, "spam")
    async def spam(event, arg):
        await say(event, "🛡 Mass-message and media-spam commands are disabled to prevent abuse and rate limits.", md=False)
