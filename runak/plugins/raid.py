import asyncio
import random
from telethon import events, functions, types
from runak.helpers import bot, safe_edit, get_targets, reply_users, rr_users, flag_users, hrr_users, replygod_users
from runak.plugins.vortex_core import register_cmd

reply_list = ["𝐊ʏᴀ 𝐑ᴇ 𝐑ᴀɴᴅɪᴋᴇ 𝐂ᴏᴏʟ 𝐁ᴀɴᴇɢᴀ 𝐓ᴜ 𝐂ʜᴀʟ 𝐀ʙ 𝐂ʜᴜᴅ 𝐀ᴘɴᴇ 𝐁ᴀᴘ - 🦢💘", "𝐊ɪ 𝐌ᴀᴀ 𝐌ᴀʀʀ 𝐆ᴀʏɪ 𝐘ᴀᴀʀ - 𝐉ᴀɪ Dʜʀᴜᴠ ! 🌙"]
fun_texts = ["तेरे मां के दूदू के बीच मेरा lund fas gaya oops 🤪", "𝐓ᴇʀʏ 𝐁ʜᴇ𝐍 𝐊ᴇ ( ͜. ㅅ ͜. )🥛 ʏᴜᴍᴍʏ"]
flag_texts = ["🇮🇳 𝐓ᴇʀɪ 𝐌ᴀᴀ 𝐊ᴇ 𝐒ᴀᴛʜ 𝐁ᴀᴀᴘ 𝐀ᴜʀ 𝐈ɴᴅɪᴀ 𝐖ᴀʟᴇ 𝐁ʜɪ 𝐂ʜɪʟʟ 𝐊ᴀʀ 𝐑ʜᴇ"]
heart_replies = ["❤️ sꪶꪖꪜꫀ ִֶָ. .. 𝗟𝗡𝗗 𝗖𝗛𝗢𝗢𝗦"]

@register_cmd("reply", needs_reply=True)
async def cmd_reply(event, arg):
    targets = await get_targets(event, arg)
    for uid in targets:
        reply_users.add(int(uid))
    await safe_edit(event, "🔥 𝐑ᴇᴘʟʏ 𝐑ᴀɪᴅ 𝐎ɴ")

@register_cmd("sreply")
async def cmd_sreply(event, _):
    reply_users.clear()
    await safe_edit(event, "🛑 𝐑ᴇᴘʟʏ 𝐑ᴀɪᴅ 𝐎ғғ")

@register_cmd("rr", needs_reply=True)
async def cmd_rr(event, arg):
    targets = await get_targets(event, arg)
    for uid in targets:
        rr_users.add(int(uid))
    await safe_edit(event, "⚡ 𝐑𝐑 𝐎ɴ")

@register_cmd("srr")
async def cmd_srr(event, _):
    rr_users.clear()
    await safe_edit(event, "🛑 𝐑𝐑 𝐎ғғ")

# Global Raid Message Listener
@bot.on(events.NewMessage)
async def raid_listener(event):
    if event.out:
        return
    sender = event.sender_id
    if not sender:
        return
        
    if sender in reply_users:
        try:
            await event.reply(random.choice(reply_list))
        except Exception:
            pass
    if sender in rr_users:
        try:
            msg = await event.reply(random.choice(fun_texts))
            await bot(functions.messages.SendReactionRequest(peer=event.chat_id, msg_id=msg.id, reaction=[types.ReactionEmoji(emoticon="🤣")]))
        except Exception:
            pass
