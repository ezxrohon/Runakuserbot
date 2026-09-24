from ..context import say

NAME = "purge"
TITLE = "🧹 Clean-up"
DESC = "Delete your own messages only — never anyone else's."
DEFAULT_ON = True
COMMANDS = [
    ("del", "Delete the replied message (if it's yours)"),
    ("purge", "Reply to a message: delete YOUR messages from there down (max 100)"),
]


def setup(ctx):
    @ctx.command(NAME, "del")
    async def delete_one(event, arg):
        reply = await event.get_reply_message()
        if reply and reply.out:
            await reply.delete()
        await event.delete()

    @ctx.command(NAME, "purge")
    async def purge(event, arg):
        reply = await event.get_reply_message()
        if not reply:
            await say(event, "Reply to the message you want to start from.")
            return
        ids = {event.id}
        async for msg in ctx.client.iter_messages(
            event.chat_id, min_id=reply.id - 1, from_user="me", limit=100
        ):
            ids.add(msg.id)
        await ctx.client.delete_messages(event.chat_id, list(ids))
