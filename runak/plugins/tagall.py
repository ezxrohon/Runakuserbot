"""Native bulk member mention plugin."""
import asyncio
from ..context import say

NAME = "tagall"
TITLE = "👥 Tag All"
DESC = "Mention group members and stop an active mention loop."
DEFAULT_ON = True
COMMANDS = [("tagall", "Mention all members"), ("cancel", "Stop tag-all")]
ACTIVE = set()


def _name(user):
    return getattr(user, "first_name", None) or getattr(user, "username", None) or "User"


def setup(ctx):
    @ctx.command(NAME, "tagall", "all")
    async def tagall(event, arg):
        if event.chat_id in ACTIVE:
            await say(event, "A tag-all is already running. Use `.cancel`.", md=False)
            return
        reply = await event.get_reply_message()
        text = arg.strip()
        if not text and not reply:
            await say(event, "Usage: `.tagall <text>` or reply to a message.", md=False)
            return
        ACTIVE.add(event.chat_id)
        try:
            body = (reply.raw_text or reply.message or "") if reply else text
            batch = []
            async for user in event.client.iter_participants(event.chat_id):
                if event.chat_id not in ACTIVE:
                    break
                batch.append(f"[{_name(user)}](tg://user?id={user.id})")
                if len(batch) >= 14:
                    await event.respond(f"{body}\n\n{' '.join(batch)}", parse_mode="md")
                    batch.clear()
                    await asyncio.sleep(1.2)
            if batch and event.chat_id in ACTIVE:
                await event.respond(f"{body}\n\n{' '.join(batch)}", parse_mode="md")
        finally:
            ACTIVE.discard(event.chat_id)

    @ctx.command(NAME, "cancel", "stopall", "offall")
    async def cancel(event, arg):
        ACTIVE.discard(event.chat_id)
        await say(event, "✅ Tag-all stopped.", md=False)
