"""Native random reaction plugin."""
import json
import random
from pathlib import Path
from telethon import events
from telethon.tl import functions, types

NAME = "autoreact"
TITLE = "😊 Auto React"
DESC = "React to incoming messages in selected chats."
DEFAULT_ON = True
COMMANDS = [("autoreact", "Enable, disable or inspect auto-react"), ("react", "React to a replied message")]
REACTIONS = ("👍", "❤", "🔥", "🥰", "👏", "😁", "🤔", "🎉", "🤩", "🙏", "💯")
STATE_FILE = Path("autoreact.json")
STATE = {"chats": {}}
try:
    STATE = json.loads(STATE_FILE.read_text(encoding="utf-8"))
except (OSError, ValueError):
    pass


def _save():
    try:
        STATE_FILE.write_text(json.dumps(STATE, indent=2), encoding="utf-8")
    except OSError:
        pass


def setup(ctx):
    @ctx.command(NAME, "autoreact")
    async def command(event, arg):
        key = str(event.chat_id)
        value = arg.strip().lower()
        if value in {"on", "enable", "start"}:
            STATE.setdefault("chats", {})[key] = True
            _save(); await ctx.client.send_message(event.chat_id, "✅ Auto-react enabled.", parse_mode=None)
        elif value in {"off", "disable", "stop"}:
            STATE.setdefault("chats", {})[key] = False
            _save(); await ctx.client.send_message(event.chat_id, "✅ Auto-react disabled.", parse_mode=None)
        else:
            status = STATE.get("chats", {}).get(key, False)
            await ctx.client.send_message(event.chat_id, f"Auto-react: {'on' if status else 'off'}", parse_mode=None)

    @ctx.command(NAME, "react", "test")
    async def test(event, arg):
        target = await event.get_reply_message() or event
        await event.client(functions.messages.SendReactionRequest(
            peer=event.chat_id, msg_id=target.id, big=False, add_to_recent=True,
            reaction=[types.ReactionEmoji(emoticon=random.choice(REACTIONS))],
        ))

    @ctx.client.on(events.NewMessage(incoming=True))
    async def watcher(event):
        if not STATE.get("chats", {}).get(str(event.chat_id), False) or event.sender_id == ctx.me.id:
            return
        if random.random() > 0.35:
            return
        try:
            await event.client(functions.messages.SendReactionRequest(
                peer=event.chat_id, msg_id=event.id, big=False, add_to_recent=True,
                reaction=[types.ReactionEmoji(emoticon=random.choice(REACTIONS))],
            ))
        except Exception:
            pass
