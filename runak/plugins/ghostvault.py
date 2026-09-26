"""Opt-in local message tracking status; no silent interception is performed."""
from ..context import say

NAME = "ghostvault"
TITLE = "👻 Ghost Vault"
DESC = "Privacy-safe status for optional message tracking."
DEFAULT_ON = False
COMMANDS = [("vault", "Show tracking status"), ("vault on|off", "Enable or disable status")]


def setup(ctx):
    state = {"on": False}

    @ctx.command(NAME, "vault")
    async def vault(event, arg):
        value = (arg or "").strip().lower()
        if value in {"on", "off"}:
            state["on"] = value == "on"
            await say(event, f"👻 Tracking status: **{'ON' if state['on'] else 'OFF'}**. No messages are copied or forwarded.")
            return
        await say(event, f"👻 Tracking status: **{'ON' if state['on'] else 'OFF'}**\nNo messages are copied or forwarded.")
