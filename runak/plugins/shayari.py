import random

from ..context import say

NAME = "shayari"
TITLE = "🌹 Shayari"
DESC = "Send a random shayari line to a chat — on demand, no auto-targeting."
DEFAULT_ON = True
COMMANDS = [
    ("shayari", "Send a random shayari (or reply to include the person's name)"),
]

LINES = [
    "ᴛᴜᴍʜᴀʀɪ ᴇᴋ ᴍᴜsᴋᴀᴀɴ ʜɪ ᴅɪʟ ᴋᴏ ᴋʜᴜsʜ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ᴋᴀᴀғɪ ʜᴀɪ ✨",
    "ᴋᴜᴄʜ ʟᴏɢ ᴢɪɴᴅᴀɢɪ ᴍᴇ ɴᴀʜɪ, ᴅɪʟ ᴍᴇ ʜᴀᴍᴇsʜᴀ ʀᴀʜᴛᴇ ʜᴀɪɴ 💕",
    "ᴅɪʟ ᴋᴇ ᴋᴀᴀʀɪʙ ᴡᴏʜɪ ʜᴏᴛᴇ ʜᴀɪɴ ᴊᴏ ᴋʜᴀᴀs ʜᴏᴛᴇ ʜᴀɪɴ 💖",
    "ᴋᴜᴄʜ ᴍᴜʟᴀᴀᴋᴀᴀᴛᴇɴ ᴄʜʜᴏᴛɪ ʜᴏᴛɪ ʜᴀɪɴ, ᴘᴀʀ ʏᴀᴀᴅᴇɪɴ ʟᴀᴍʙɪ ʜᴏᴛɪ ʜᴀɪɴ ❤️",
    "ᴛᴜᴍ ᴘᴀᴀs ʜᴏ ʏᴀ ᴅᴜᴜʀ, ᴅɪʟ ᴍᴇ ᴛᴜᴍʜᴀʀɪ ᴊᴀɢᴀʜ ʜᴀᴍᴇsʜᴀ ʜᴀɪ 💞",
    "ᴛᴜᴍʜᴀʀɪ ʜᴀʀ ʙᴀᴀᴛ ᴍᴇ ᴋᴜᴄʜ ᴋʜᴀᴀs sᴀ ᴀʜsᴀᴀs ʜᴏᴛᴀ ʜᴀɪ 💖",
]


def setup(ctx):
    @ctx.command(NAME, "shayari")
    async def shayari(event, arg):
        line = random.choice(LINES)
        name = None
        if event.is_reply:
            replied = await event.get_reply_message()
            sender = await replied.get_sender()
            if sender:
                name = sender.first_name

        text = f"💖 **{name.upper()}** 💖\n\n{line}" if name else f"💖 {line}"
        await say(event, text)
