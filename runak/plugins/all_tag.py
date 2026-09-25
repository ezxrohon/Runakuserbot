"""Compatibility alias for the historical ``.king`` command."""
from .tagall import ACTIVE, _name
from ..context import say

NAME = "all_tag"
TITLE = "👑 King Mention"
DESC = "Mention group members with the legacy king command."
DEFAULT_ON = True
COMMANDS = [("king", "Mention all members"), ("kingoff", "Stop king mentions")]


def setup(ctx):
    @ctx.command(NAME, "king")
    async def king(event, arg):
        # Reuse the native implementation without importing Pyrogram.
        if event.chat_id in ACTIVE:
            await say(event, "A mention loop is already running. Use `.kingoff`.", md=False)
            return
        if not arg and not await event.get_reply_message():
            await say(event, "Usage: `.king <text>` or reply to a message.", md=False)
            return
        ACTIVE.add(event.chat_id)
        try:
            reply = await event.get_reply_message()
            body = (reply.raw_text or reply.message or "") if reply else arg
            batch = []
            async for user in event.client.iter_participants(event.chat_id):
                if event.chat_id not in ACTIVE:
                    break
                batch.append(f"[{_name(user)}](tg://user?id={user.id})")
                if len(batch) >= 14:
                    await event.respond(f"{body}\n\n{' '.join(batch)}", parse_mode="md")
                    batch.clear()
            if batch and event.chat_id in ACTIVE:
                await event.respond(f"{body}\n\n{' '.join(batch)}", parse_mode="md")
        finally:
            ACTIVE.discard(event.chat_id)

    @ctx.command(NAME, "kingoff", "allstop", "allcancel")
    async def stop(event, arg):
        ACTIVE.discard(event.chat_id)
        await say(event, "✅ King mention stopped.", md=False)
