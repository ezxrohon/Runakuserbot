"""`.auth @username` — choose who else may use your userbot.

Only your own outgoing messages can run commands. `.auth` lets you extend that to specific people:
they can then open the control bot (/start, /help, /login) — and nothing else. They can never run
userbot commands. Everyone you have not authorised is ignored. Only you can add or remove people.
"""
from .. import config as cfg
from ..context import say

NAME = "auth"
TITLE = "🔐 Auth"
DESC = "Choose who else may open the control bot (/start, /help, /login)."
DEFAULT_ON = True
LOCKED = True

COMMANDS = [
    ("auth @username", "Allow someone to use your userbot (or reply to them with .auth)"),
    ("unauth @username", "Remove someone's access"),
    ("authlist", "Show who is authorised"),
]


def setup(ctx):
    async def resolve(event, arg):
        """Return a user entity from a reply, an @username or a numeric id."""
        arg = arg.strip()
        if not arg:
            reply = await event.get_reply_message()
            return await reply.get_sender() if reply else None
        ref = int(arg) if arg.lstrip("-").isdigit() else arg
        try:
            return await ctx.client.get_entity(ref)
        except Exception:
            return None

    def label(user) -> str:
        return f"@{user.username}" if getattr(user, "username", None) else (getattr(user, "first_name", None) or str(user.id))

    @ctx.command(NAME, "auth", always=True)
    async def auth(event, arg):
        user = await resolve(event, arg)
        if user is None or not hasattr(user, "first_name"):
            await say(event, f"Usage: `{cfg.PREFIX}auth @username` (or reply to the person with `{cfg.PREFIX}auth`).")
            return
        if user.id == ctx.me.id:
            await say(event, "You're the owner — you already have full access.")
            return
        if getattr(user, "bot", False):
            await say(event, "Bots can't be authorised.")
            return
        ctx.store.data["auth"]["users"][str(user.id)] = label(user)
        ctx.store.save_soon()
        await say(
            event,
            f"✅ **{label(user)}** is now authorised.\n\n"
            "They can open the bot (/start, /help, /login). No other access.\n\n"
            f"Remove them with `{cfg.PREFIX}unauth @username`.\n"
            f"See who is authorised with `{cfg.PREFIX}authlist`.",
        )

    @ctx.command(NAME, "unauth", always=True)
    async def unauth(event, arg):
        users = ctx.store.data["auth"]["users"]
        user = await resolve(event, arg)
        key = str(user.id) if user is not None and hasattr(user, "first_name") else None
        if key is None and arg.lstrip("@").lower() in {v.lstrip("@").lower() for v in users.values()}:
            key = next(k for k, v in users.items() if v.lstrip("@").lower() == arg.lstrip("@").lower())
        if key is None or key not in users:
            await say(event, "That person isn't authorised.")
            return
        name = users.pop(key)
        ctx.store.save_soon()
        await say(event, f"🚫 **{name}** can no longer use your userbot.")

    @ctx.command(NAME, "authlist", always=True)
    async def authlist(event, arg):
        users = ctx.store.data["auth"]["users"]
        if not users:
            await say(event, "Nobody else is authorised. Only you can use this userbot.")
            return
        lines = [f"• {name} (`{uid}`)" for uid, name in users.items()]
        await say(event, "**🔐 Authorised users**\n" + "\n".join(lines))
