from telethon import TelegramClient, events
import random

API_ID = 33856248
API_HASH = 27bd3006cfb0c0b38bf209132dd6fe1d

client = TelegramClient("love_session", API_ID, API_HASH)

target_user = None

SHAYARI = [
    "💖 ᴛᴜᴍʜᴀʀɪ ᴇᴋ ᴍᴜsᴋᴀᴀɴ ʜɪ ᴅɪʟ ᴋᴏ ᴋʜᴜsʜ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ᴋᴀᴀғɪ ʜᴀɪ ✨",
    "🌹 ᴋᴜᴄʜ ʟᴏɢ ᴢɪɴᴅᴀɢɪ ᴍᴇ ɴᴀʜɪ, ᴅɪʟ ᴍᴇ ʜᴀᴍᴇsʜᴀ ʀᴀʜᴛᴇ ʜᴀɪɴ 💕",
    "💫 ᴛᴜᴍʜᴀʀᴇ ᴍᴇssᴀɢᴇ ᴋᴀ ɪɴᴛᴇᴢᴀᴀʀ ʜᴀʀ ʙᴀᴀʀ ʀᴇʜᴛᴀ ʜᴀɪ 💗",
    "🦋 ᴅɪʟ ᴋᴇ ᴋᴀᴀʀɪʙ ᴡᴏʜɪ ʜᴏᴛᴇ ʜᴀɪɴ ᴊᴏ ᴋʜᴀᴀs ʜᴏᴛᴇ ʜᴀɪɴ 💖",
    "🌙 ᴛᴜᴍʜᴀʀᴀ ɴᴀᴀᴍ ᴀᴀᴛᴇ ʜɪ ᴄʜᴇʜʀᴇ ᴘᴀʀ ᴍᴜsᴋᴀᴀɴ ᴀᴀ ᴊᴀᴀᴛɪ ʜᴀɪ ✨",
    "🥀 ᴋᴜᴄʜ ᴍᴜʟᴀᴀᴋᴀᴀᴛᴇɴ ᴄʜʜᴏᴛɪ ʜᴏᴛɪ ʜᴀɪɴ, ᴘᴀʀ ʏᴀᴀᴅᴇɪɴ ʟᴀᴍʙɪ ʜᴏᴛɪ ʜᴀɪɴ ❤️",
    "💐 ᴛᴜᴍ ᴘᴀᴀs ʜᴏ ʏᴀ ᴅᴜᴜʀ, ᴅɪʟ ᴍᴇ ᴛᴜᴍʜᴀʀɪ ᴊᴀɢᴀʜ ʜᴀᴍᴇsʜᴀ ʜᴀɪ 💞",
    "⭐ ᴛᴜᴍʜᴀʀɪ ʜᴀʀ ʙᴀᴀᴛ ᴍᴇ ᴋᴜᴄʜ ᴋʜᴀᴀs sᴀ ᴀʜsᴀᴀs ʜᴏᴛᴀ ʜᴀɪ 💖"
]


@client.on(events.NewMessage)
async def handler(event):
    global target_user

    text = event.raw_text.strip()

    # /love — reply karke target select
    if text.lower() == "/love":
        if not event.is_reply:
            await event.reply(
                "💖 ᴋɪsɪ ᴜsᴇʀ ᴋᴇ ᴍᴇssᴀɢᴇ ᴋᴏ ʀᴇᴘʟʏ ᴋᴀʀᴋᴇ /love ʟɪᴋʜᴏ ✨"
            )
            return

        replied = await event.get_reply_message()
        sender = await replied.get_sender()

        if not sender:
            await event.reply("❌ ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ")
            return

        target_user = sender.id
        name = sender.first_name or "USER"

        await event.reply(
            f"💖 ʟᴏᴠᴇ ᴛᴀʀɢᴇᴛ sᴇᴛ 💖\n\n"
            f"👤 {name}\n"
            f"✨ ᴀʙ ʜᴀʀ ᴍᴇssᴀɢᴇ ᴘᴀʀ sʜᴀʏᴀʀɪ ᴀᴀʏᴇɢɪ 💕"
        )
        return

    # /song SONG LINK/TEXT
    if text.lower().startswith("/song"):
        if not target_user:
            await event.reply("❌ ᴘᴇʜʟᴇ /love sᴇ ᴛᴀʀɢᴇᴛ sᴇᴛ ᴋᴀʀᴏ 💖")
            return

        song = text[5:].strip()

        if not song:
            await event.reply(
                "🎵 ᴜsᴇ:\n/song Song Name / Song Link"
            )
            return

        try:
            user = await client.get_entity(target_user)

            await client.send_message(
                event.chat_id,
                f"🎵💖 {user.first_name or 'USER'} 💖🎵\n\n"
                f"✨ ʏᴇ sᴏɴɢ ᴛᴜᴍʜᴀʀᴇ ʟɪʏᴇ 🌙\n\n"
                f"🎶 {song}",
                reply_to=event.id
            )

        except Exception as e:
            await event.reply(f"❌ sᴏɴɢ sᴇɴᴅ ᴇʀʀᴏʀ: {e}")

        return

    # /stop — sab automation stop
    if text.lower() == "/stop":
        target_user = None

        await event.reply(
            "🛑💔 ʟᴏᴠᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴏɴ sᴛᴏᴘᴘᴇᴅ 💔🛑"
        )
        return

    # Target ke har message par shayari
    if target_user and event.sender_id == target_user:

        sender = await event.get_sender()

        if sender:
            name = sender.first_name or "USER"
            shayari = random.choice(SHAYARI)

            await event.reply(
                f"💖 {name.upper()} 💖\n\n"
                f"{shayari}"
            )


print("💖 LOVE AUTOMATION STARTED...")

client.start()

print("✅ LOGIN SUCCESSFUL!")

client.run_until_disconnected()
