"""Safe, local replacement for the old third-party Play Store scraper."""
from urllib.parse import quote_plus
from ..context import say

NAME = "playstore"
TITLE = "📱 Play Store"
DESC = "Build a Play Store search link without scraping or extra dependencies."
DEFAULT_ON = True
COMMANDS = [("app <name>", "Open a Play Store search link")]


def setup(ctx):
    @ctx.command(NAME, "app")
    async def app(event, arg):
        query = " ".join(arg.split())
        if not query:
            await say(event, "Usage: `.app telegram`", md=False)
            return
        url = "https://play.google.com/store/search?q=" + quote_plus(query) + "&c=apps"
        await say(event, f"📱 **Play Store search**\n[{query}]({url})", md=True)
