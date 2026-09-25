"""Opt-in love/shayari replies, attached to the current Runak account."""
import random

from ..context import say

NAME = "love"
TITLE = "💖 Love Replies"
DESC = "Reply with a poem when one selected person sends a DM."
DEFAULT_ON = False
COMMANDS = [("love", "Reply to a user's message to select them"), ("loveoff", "Stop love replies")]
POEMS = ["Tumhari ek muskaan hi dil ko khush karne ke liye kaafi hai. 💖", "Kuch mulaqatein chhoti hoti hain, yaadein lambi. 🌹"]


def setup(ctx):
    target = {"id": None}

    @ctx.command(NAME, "love")
    async def enable(event, arg):
        if not event.is_reply:
            await say(event, "Reply to a user's message, then send `.love`.", md=False)
            return
        reply = await event.get_reply_message()
        sender = await reply.get_sender() if reply else None
        if not sender or sender.id == ctx.me.id:
            await say(event, "❌ User not found.", md=False)
            return
        target["id"] = sender.id
        await say(event, "💖 Love replies enabled for this user.", md=False)

    @ctx.command(NAME, "loveoff")
    async def disable(event, arg):
        target["id"] = None
        await say(event, "🛑 Love replies stopped.", md=False)

    @ctx.on_dm(NAME)
    async def reply(event):
        if target["id"] == event.sender_id:
            await event.respond(random.choice(POEMS))
