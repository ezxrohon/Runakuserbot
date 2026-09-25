"""Native replacement for the incompatible legacy raid module.

The old module imported another userbot framework and automated harassment.  This
plugin keeps the command discoverable without sending unsolicited messages.
"""
from ..context import say

NAME = "raid"
TITLE = "🛡 Raid Protection"
DESC = "Explains why automated harassment raids are unavailable."
DEFAULT_ON = False
COMMANDS = [("raid", "Show raid protection status")]


def setup(ctx):
    @ctx.command(NAME, "raid")
    async def raid(event, arg):
        await say(event, "🛡 Automated harassment raids are not available. Use normal, consent-based messages instead.", md=False)
