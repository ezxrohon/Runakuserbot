import os
import json
import time
from telethon import events, functions
from runak.helpers import bot, OWNER_ID, admins, save_admins, safe_edit, get_targets, menu_banner_msg, BANNER_FILE

commands = {}

def register_cmd(name: str, needs_reply: bool = False, group_only: bool = False):
    def decorator(func):
        key = (name or "").lower().strip()
        commands[key] = {"func": func, "needs_reply": needs_reply, "group_only": group_only}
        return func
    return decorator

@register_cmd("ping")
async def cmd_ping(event, _):
    t0 = time.perf_counter()
    msg = await event.edit("🏓 𝐏ɪɴɢ...") if event.out else await event.reply("🏓 𝐏ɪɴɢ...")
    ms = round((time.perf_counter() - t0) * 1000)
    await msg.edit(f"🏓 𝐏ᴏɴɢ → `{ms} ms`\n👑 RUNAK\n💎 Powered by Runak ")

@register_cmd("owner")
async def cmd_owner(event, _):
    await safe_edit(event, "╔═══════ 👑 𝐎𝐖𝐍𝐄𝐑 👑 ═══════╗\n┃ ⚡ RUNAK USERBOT\n┃ 💎 REPO: Runak / Blood Vortex\n╚══════════════════════════╝")

@register_cmd("admins")
async def cmd_admins(event, _):
    admin_list = "\n".join(f"• `{a}`" for a in sorted(admins)) if admins else "⚠️ 𝐍ᴏ 𝐄xᴛʀᴀ 𝐀ᴅᴍɪɴs"
    await safe_edit(event, f"👑 𝐀ᴅᴍɪɴ 𝐋ɪsᴛ\n━━━━━━━━━━━━━━━\n👑 𝐎ᴡɴᴇʀ → `{OWNER_ID}`\n\n{admin_list}\n\n📊 𝐓ᴏᴛᴀʟ → `{len(admins)}`")

# Unified Command Dispatcher
@bot.on(events.NewMessage)
async def plugin_dispatcher(event):
    text = event.raw_text
    if not text or not text.startswith("."):
        return
    body = text[1:].strip()
    if not body:
        return
    parts = body.split(maxsplit=1)
    cmd, arg = parts[0].lower().strip(), parts[1].strip() if len(parts) > 1 else ""
    
    cmd_data = commands.get(cmd)
    if not cmd_data:
        return
    
    sender = event.sender_id
    if not sender:
        return
        
    if sender != OWNER_ID and sender not in admins:
        return
        
    if cmd_data.get("group_only") and not event.is_group:
        return await safe_edit(event, "⚠️ 𝐆ʀᴏᴜᴘ 𝐎ɴʟʏ 𝐂ᴏᴍᴍᴀɴᴅ")
        
    try:
        await cmd_data["func"](event, arg)
    except Exception as e:
        await safe_edit(event, f"❌ 𝐄ʀʀᴏʀ → `{str(e)[:50]}`")
