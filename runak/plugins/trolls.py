"""Offline troll/meme placeholder with no third-party uploads."""
from ..context import say

NAME = "trolls"
TITLE = "😈 Trolls"
DESC = "Safe local reactions; no image uploads to third-party services."
DEFAULT_ON = False
COMMANDS = [("troll", "Show a harmless reaction")]


def setup(ctx):
    @ctx.command(NAME, "troll")
    async def troll(event, arg):
        await say(event, "😈 Nice try — third-party meme uploads are disabled. Use a local editor instead.", md=False)
