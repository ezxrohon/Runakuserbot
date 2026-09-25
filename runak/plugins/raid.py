"""Non-abusive raid replacement.

Automatic harassment of other users was removed.  The command now produces a
single playful, opt-in-free banner and never watches or replies to strangers.
"""
from ..context import say

NAME = "raid"
TITLE = "🎭 Raid"
DESC = "Show a harmless raid banner; no automatic harassment."
DEFAULT_ON = False
COMMANDS = [("raid", "Show a harmless raid banner"), ("draid", "Remove the banner")]


def setup(ctx):
    @ctx.command(NAME, "raid")
    async def raid(event, arg):
        await say(event, "🎭 **Raid mode preview**\nNo automatic messages will be sent to anyone.", md=False)

    @ctx.command(NAME, "draid")
    async def stop(event, arg):
        await say(event, "✅ Raid mode is inactive.", md=False)
