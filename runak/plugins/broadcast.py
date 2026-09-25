"""Native broadcast plugin for replied messages."""
import asyncio
from telethon.tl.types import Channel, Chat, User
from ..context import say

NAME = "broadcast"
TITLE = "📡 Broadcast"
DESC = "Forward or copy a replied message to selected dialogs."
DEFAULT_ON = True
COMMANDS = [("gcast", "Broadcast a replied message"), ("bstats", "Show dialog counts")]


def setup(ctx):
    @ctx.command(NAME, "gcast")
    async def gcast(event, arg):
        reply = await event.get_reply_message()
        if not reply:
            await say(event, "Reply to a message first.", md=False); return
        parts = (arg or "groups").split()
        target = parts[0].lower() if parts else "groups"
        copy = "copy" in [p.lower() for p in parts[1:]]
        if target not in {"all", "groups", "users"}:
            await say(event, "Usage: `.gcast all|groups|users [copy]`", md=False); return
        dialogs = []
        async for dialog in event.client.iter_dialogs():
            entity = dialog.entity
            if target == "all" or (target == "groups" and isinstance(entity, (Chat, Channel)) and not getattr(entity, "broadcast", False)) or (target == "users" and isinstance(entity, User) and not entity.bot):
                dialogs.append(dialog)
        sent = 0
        for dialog in dialogs:
            try:
                if copy:
                    await event.client.send_message(dialog.id, reply.message or "", file=reply.media)
                else:
                    await event.client.forward_messages(dialog.id, reply)
                sent += 1
            except Exception:
                pass
            await asyncio.sleep(0.1)
        await say(event, f"✅ Broadcast sent to {sent}/{len(dialogs)} dialogs.", md=False)

    @ctx.command(NAME, "bstats")
    async def stats(event, arg):
        total = groups = users = 0
        async for dialog in event.client.iter_dialogs():
            total += 1; entity = dialog.entity
            if isinstance(entity, User) and not entity.bot: users += 1
            elif isinstance(entity, (Chat, Channel)) and not getattr(entity, "broadcast", False): groups += 1
        await say(event, f"Dialogs: {total}\nUsers: {users}\nGroups: {groups}", md=False)
