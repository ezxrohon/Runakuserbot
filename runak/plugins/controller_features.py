"""Premium controller features for Runak.

Includes:
- Target reply / mute / lock
- Rotating group and DM replies
- Group/DM mute and lock controls
- Persistent settings
- Spam-burst protection
- Raid-burst protection
- Status and stop-all controls

The spam/raid functionality is defensive protection. It does not generate
mass messages or perform raid/flood attacks.
"""

import asyncio
import time
from collections import defaultdict, deque

from telethon import events

from ..context import say

NAME = "controller_features"
TITLE = "⚡ Multi-Account Control"
DESC = (
    "Target rules, group/DM automation, diagnostics, "
    "and anti-spam/raid protection."
)
DEFAULT_ON = True

COMMANDS = [
    ("target", "Set a target rule: reply, mute, or lock"),
    ("stoptarget", "Remove a target rule"),
    ("targetreply", "Enable target auto-reply"),
    ("targetmute", "Enable target mute"),
    ("targetlock", "Enable target lock"),
    ("stoptargetreply", "Stop target reply"),
    ("stoptargetmute", "Stop target mute"),
    ("stoptargetlock", "Stop target lock"),
    ("replyall", "Enable group rotating replies"),
    ("stopreplyall", "Disable group rotating replies"),
    ("mutegc", "Enable group message protection"),
    ("stopmutegc", "Disable group message protection"),
    ("lockall", "Enable group lock protection"),
    ("stoplockall", "Disable group lock protection"),
    ("reply", "Enable automatic replies"),
    ("stopreply", "Disable automatic replies"),
    ("mute", "Enable mute protection"),
    ("stopmute", "Disable mute protection"),
    ("muteall", "Enable global DM mute"),
    ("stopmuteall", "Disable global DM mute"),
    ("lock", "Enable chat lock protection"),
    ("stoplock", "Disable chat lock protection"),
    ("gcmsgs", "Show group reply messages"),
    ("dmmsgs", "Show DM reply messages"),
    ("setgc", "Set a group reply"),
    ("setdm", "Set a DM reply"),
    ("stopall", "Stop controller rules in this chat"),
    ("spam", "Toggle spam-burst protection"),
    ("raid", "Toggle raid-burst protection"),
    ("status", "Show controller status"),
]


GC_DEFAULTS = [
    "Please keep the conversation respectful.",
    "Please avoid repeated messages.",
    "Please slow down and keep the chat readable.",
    "Please follow the group rules.",
    "Message received — keeping the chat calm.",
]

DM_DEFAULTS = [
    "I am currently unavailable.",
    "Please leave your message and I will check it later.",
    "Thanks for your message.",
    "I will reply when I am available.",
    "Please avoid sending repeated messages.",
]


STATE = {}


def _state(ctx):
    """Return/create state for one account context."""
    return STATE.setdefault(
        id(ctx),
        {
            "loaded": False,
            "targets": {
                "reply": set(),
                "mute": set(),
                "lock": set(),
            },
            "reply_chats": set(),
            "mute_chats": set(),
            "lock_chats": set(),
            "unmute": set(),
            "mute_all": False,
            "gc": list(GC_DEFAULTS),
            "dm": list(DM_DEFAULTS),
            "gc_index": defaultdict(int),
            "dm_index": defaultdict(int),
            "last_reply": {},
            "spam": set(),
            "raid": set(),
            "events": defaultdict(lambda: defaultdict(deque)),
        },
    )


def _persist(ctx, st):
    """Persist configuration through the existing Runak Store."""
    ctx.store.data.setdefault("controller", {})

    ctx.store.data["controller"] = {
        "targets": {
            key: list(value)
            for key, value in st["targets"].items()
        },
        "reply_chats": list(st["reply_chats"]),
        "mute_chats": list(st["mute_chats"]),
        "lock_chats": list(st["lock_chats"]),
        "unmute": list(st["unmute"]),
        "mute_all": st["mute_all"],
        "gc": st["gc"][:5],
        "dm": st["dm"][:5],
        "spam": list(st["spam"]),
        "raid": list(st["raid"]),
    }

    ctx.store.save_soon()


def _load(ctx, st):
    """Load persisted controller settings."""
    if st["loaded"]:
        return

    st["loaded"] = True

    data = ctx.store.data.get("controller", {})

    targets = data.get("targets", {})

    for key in st["targets"]:
        for value in targets.get(key, []):
            try:
                st["targets"][key].add(int(value))
            except (TypeError, ValueError):
                continue

    for key in (
        "reply_chats",
        "mute_chats",
        "lock_chats",
        "unmute",
        "spam",
        "raid",
    ):
        for value in data.get(key, []):
            try:
                st[key].add(int(value))
            except (TypeError, ValueError):
                continue

    st["mute_all"] = bool(data.get("mute_all", False))

    if isinstance(data.get("gc"), list) and len(data["gc"]) >= 5:
        st["gc"] = [str(x) for x in data["gc"][:5]]

    if isinstance(data.get("dm"), list) and len(data["dm"]) >= 5:
        st["dm"] = [str(x) for x in data["dm"][:5]]


async def _resolve_targets(event, argument):
    """Resolve replied user and explicit usernames/IDs."""
    users = []

    try:
        reply = await event.get_reply_message()
    except Exception:
        reply = None

    if reply and getattr(reply, "sender_id", None):
        users.append(int(reply.sender_id))

    for token in (argument or "").replace(",", " ").split():
        try:
            if token.lstrip("-").isdigit():
                entity = await event.client.get_entity(int(token))
            else:
                entity = await event.client.get_entity(token)

            user_id = getattr(entity, "id", None)

            if user_id is not None:
                user_id = int(user_id)

                if user_id not in users:
                    users.append(user_id)

        except Exception:
            continue

    return users


async def _restrict(ctx, event, user_id, seconds=600):
    """Attempt a temporary restriction where Telegram permissions allow it."""
    try:
        await event.client.edit_permissions(
            event.chat_id,
            user_id,
            send_messages=False,
            until_date=time.time() + seconds,
        )
        return True
    except Exception:
        return False


def _value(argument):
    return (argument or "").strip().lower()


def setup(ctx):
    """Register controller commands and defensive message protection."""
    st = _state(ctx)
    _load(ctx, st)

    @ctx.command(NAME, "target")
    async def target(event, arg):
        parts = (arg or "").split(maxsplit=1)

        if not parts or parts[0].lower() not in {
            "reply",
            "mute",
            "lock",
        }:
            await say(
                event,
                "Usage: `.target reply|mute|lock @user/id`",
                md=False,
            )
            return

        kind = parts[0].lower()
        argument = parts[1] if len(parts) > 1 else ""

        users = await _resolve_targets(event, argument)

        if not users:
            await say(
                event,
                "Reply to a user or provide an @username/user ID.",
                md=False,
            )
            return

        st["targets"][kind].update(users)
        _persist(ctx, st)

        await say(
            event,
            f"✅ Target {kind} enabled for {len(users)} user(s).",
            md=False,
        )

    @ctx.command(NAME, "stoptarget")
    async def stoptarget(event, arg):
        parts = (arg or "").split(maxsplit=1)

        if not parts or parts[0].lower() not in {
            "reply",
            "mute",
            "lock",
        }:
            await say(
                event,
                "Usage: `.stoptarget reply|mute|lock @user/id`",
                md=False,
            )
            return

        kind = parts[0].lower()
        argument = parts[1] if len(parts) > 1 else ""

        users = await _resolve_targets(event, argument)

        if users:
            st["targets"][kind].difference_update(users)
        else:
            st["targets"][kind].clear()

        _persist(ctx, st)

        await say(
            event,
            f"✅ Target {kind} stopped.",
            md=False,
        )

    @ctx.command(NAME, "targetreply")
    async def targetreply(event, arg):
        users = await _resolve_targets(event, arg)

        if not users:
            await say(
                event,
                "Usage: reply to a user or use `.targetreply @user`",
                md=False,
            )
            return

        st["targets"]["reply"].update(users)
        _persist(ctx, st)

        await say(
            event,
            f"✅ Target reply enabled for {len(users)} user(s).",
            md=False,
        )

    @ctx.command(NAME, "targetmute")
    async def targetmute(event, arg):
        users = await _resolve_targets(event, arg)

        if not users:
            await say(
                event,
                "Usage: reply to a user or use `.targetmute @user`",
                md=False,
            )
            return

        st["targets"]["mute"].update(users)
        _persist(ctx, st)

        await say(
            event,
            f"✅ Target mute enabled for {len(users)} user(s).",
            md=False,
        )

    @ctx.command(NAME, "targetlock")
    async def targetlock(event, arg):
        users = await _resolve_targets(event, arg)

        if not users:
            await say(
                event,
                "Usage: reply to a user or use `.targetlock @user`",
                md=False,
            )
            return

        st["targets"]["lock"].update(users)
        _persist(ctx, st)

        await say(
            event,
            f"🔒 Target lock enabled for {len(users)} user(s).",
            md=False,
        )

    @ctx.command(NAME, "stoptargetreply")
    async def stoptargetreply(event, arg):
        users = await _resolve_targets(event, arg)

        if users:
            st["targets"]["reply"].difference_update(users)
        else:
            st["targets"]["reply"].clear()

        _persist(ctx, st)
        await say(event, "✅ Target reply stopped.", md=False)

    @ctx.command(NAME, "stoptargetmute")
    async def stoptargetmute(event, arg):
        users = await _resolve_targets(event, arg)

        if users:
            st["targets"]["mute"].difference_update(users)
        else:
            st["targets"]["mute"].clear()

        _persist(ctx, st)
        await say(event, "✅ Target mute stopped.", md=False)

    @ctx.command(NAME, "stoptargetlock")
    async def stoptargetlock(event, arg):
        users = await _resolve_targets(event, arg)

        if users:
            st["targets"]["lock"].difference_update(users)
        else:
            st["targets"]["lock"].clear()

        _persist(ctx, st)
        await say(event, "✅ Target lock stopped.", md=False)

    @ctx.command(NAME, "replyall")
    async def replyall(event, arg):
        st["reply_chats"].add(event.chat_id)
        _persist(ctx, st)

        await say(
            event,
            "⚡ Group ReplyAll ON — 5-message rotation active.",
            md=False,
        )

    @ctx.command(NAME, "stopreplyall")
    async def stopreplyall(event, arg):
        st["reply_chats"].discard(event.chat_id)
        _persist(ctx, st)

        await say(event, "✅ Group ReplyAll OFF.", md=False)

    @ctx.command(NAME, "mutegc")
    async def mutegc(event, arg):
        st["mute_chats"].add(event.chat_id)
        st["unmute"].discard(event.chat_id)
        _persist(ctx, st)

        await say(event, "🔇 Group mute protection ON.", md=False)

    @ctx.command(NAME, "stopmutegc")
    async def stopmutegc(event, arg):
        st["mute_chats"].discard(event.chat_id)
        st["unmute"].add(event.chat_id)
        _persist(ctx, st)

        await say(event, "🔊 Group mute protection OFF.", md=False)

    @ctx.command(NAME, "lockall")
    async def lockall(event, arg):
        st["lock_chats"].add(event.chat_id)
        _persist(ctx, st)

        await say(event, "🔒 Group lock protection ON.", md=False)

    @ctx.command(NAME, "stoplockall")
    async def stoplockall(event, arg):
        st["lock_chats"].discard(event.chat_id)
        _persist(ctx, st)

        await say(event, "🔓 Group lock protection OFF.", md=False)

    @ctx.command(NAME, "reply")
    async def reply(event, arg):
        st["reply_chats"].add(event.chat_id)
        _persist(ctx, st)

        await say(
            event,
            "💬 Auto-reply ON — 5-message rotation active.",
            md=False,
        )

    @ctx.command(NAME, "stopreply")
    async def stopreply(event, arg):
        st["reply_chats"].discard(event.chat_id)
        _persist(ctx, st)

        await say(event, "✅ Auto-reply OFF.", md=False)

    @ctx.command(NAME, "mute")
    async def mute(event, arg):
        st["mute_chats"].add(event.chat_id)
        st["unmute"].discard(event.chat_id)
        _persist(ctx, st)

        await say(event, "🔇 Mute ON.", md=False)

    @ctx.command(NAME, "stopmute")
    async def stopmute(event, arg):
        st["mute_chats"].discard(event.chat_id)
        st["unmute"].add(event.chat_id)
        _persist(ctx, st)

        await say(event, "🔊 Mute OFF.", md=False)

    @ctx.command(NAME, "muteall")
    async def muteall(event, arg):
        st["mute_all"] = True
        _persist(ctx, st)

        await say(
            event,
            "🔇 Global DM mute ON. Use `.stopmuteall` to disable.",
            md=False,
        )

    @ctx.command(NAME, "stopmuteall")
    async def stopmuteall(event, arg):
        st["mute_all"] = False
        st["unmute"].clear()
        _persist(ctx, st)

        await say(event, "🔊 Global DM mute OFF.", md=False)

    @ctx.command(NAME, "lock")
    async def lock(event, arg):
        st["lock_chats"].add(event.chat_id)
        _persist(ctx, st)

        await say(event, "🔒 Lock ON.", md=False)

    @ctx.command(NAME, "stoplock")
    async def stoplock(event, arg):
        st["lock_chats"].discard(event.chat_id)
        _persist(ctx, st)

        await say(event, "🔓 Lock OFF.", md=False)

    @ctx.command(NAME, "gcmsgs")
    async def gcmsgs(event, arg):
        text = "\n".join(
            f"{index + 1}. {message}"
            for index, message in enumerate(st["gc"])
        )

        await say(event, text, md=False)

    @ctx.command(NAME, "dmmsgs")
    async def dmmsgs(event, arg):
        text = "\n".join(
            f"{index + 1}. {message}"
            for index, message in enumerate(st["dm"])
        )

        await say(event, text, md=False)

    @ctx.command(NAME, "setgc")
    async def setgc(event, arg):
        parts = (arg or "").split(maxsplit=1)

        if (
            len(parts) != 2
            or not parts[0].isdigit()
            or not 1 <= int(parts[0]) <= 5
        ):
            await say(
                event,
                "Usage: `.setgc <1-5> <message>`",
                md=False,
            )
            return

        st["gc"][int(parts[0]) - 1] = parts[1]
        _persist(ctx, st)

        await say(event, "✅ Group reply updated.", md=False)

    @ctx.command(NAME, "setdm")
    async def setdm(event, arg):
        parts = (arg or "").split(maxsplit=1)

        if (
            len(parts) != 2
            or not parts[0].isdigit()
            or not 1 <= int(parts[0]) <= 5
        ):
            await say(
                event,
                "Usage: `.setdm <1-5> <message>`",
                md=False,
            )
            return

        st["dm"][int(parts[0]) - 1] = parts[1]
        _persist(ctx, st)

        await say(event, "✅ DM reply updated.", md=False)

    @ctx.command(NAME, "stopall")
    async def stopall(event, arg):
        chat_id = event.chat_id

        st["reply_chats"].discard(chat_id)
        st["mute_chats"].discard(chat_id)
        st["lock_chats"].discard(chat_id)
        st["unmute"].discard(chat_id)

        for key in st["targets"]:
            st["targets"][key].clear()

        _persist(ctx, st)

        await say(
            event,
            "🛑 All controller rules stopped for this chat.",
            md=False,
        )

    @ctx.command(NAME, "spam")
    async def spam(event, arg):
        value = _value(arg)

        if value in {"on", "enable", "1"}:
            st["spam"].add(event.chat_id)
        elif value in {"off", "disable", "0"}:
            st["spam"].discard(event.chat_id)

        _persist(ctx, st)

        state = "ON" if event.chat_id in st["spam"] else "OFF"

        await say(
            event,
            f"🛡 Spam protection: {state}",
            md=False,
        )

    @ctx.command(NAME, "raid")
    async def raid(event, arg):
        value = _value(arg)

        if value in {"on", "enable", "1"}:
            st["raid"].add(event.chat_id)
        elif value in {"off", "disable", "0"}:
            st["raid"].discard(event.chat_id)

        _persist(ctx, st)

        state = "ON" if event.chat_id in st["raid"] else "OFF"

        await say(
            event,
            f"🛡 Raid-burst protection: {state}",
            md=False,
        )

    @ctx.command(NAME, "status")
    async def status(event, arg):
        chat_id = event.chat_id

        text = (
            "⚡ CONTROLLER STATUS\n\n"
            f"🎯 Target reply: "
            f"{'ON' if st['targets']['reply'] else 'OFF'}\n"
            f"🔇 Target mute: "
            f"{'ON' if st['targets']['mute'] else 'OFF'}\n"
            f"🔒 Target lock: "
            f"{'ON' if st['targets']['lock'] else 'OFF'}\n"
            f"💬 ReplyAll: "
            f"{'ON' if chat_id in st['reply_chats'] else 'OFF'}\n"
            f"🔇 Mute: "
            f"{'ON' if chat_id in st['mute_chats'] else 'OFF'}\n"
            f"🔒 Lock: "
            f"{'ON' if chat_id in st['lock_chats'] else 'OFF'}\n"
            f"🌐 MuteAll: "
            f"{'ON' if st['mute_all'] else 'OFF'}\n"
            f"🛡 Spam protection: "
            f"{'ON' if chat_id in st['spam'] else 'OFF'}\n"
            f"🛡 Raid protection: "
            f"{'ON' if chat_id in st['raid'] else 'OFF'}"
        )

        await say(event, text, md=False)

    @ctx.client.on(events.NewMessage(incoming=True))
    async def controller_incoming(event):
        """Defensive spam/raid detection and configured automation."""
        if not ctx.enabled(NAME):
            return

        sender_id = getattr(event, "sender_id", None)

        if sender_id is None:
            return

        if sender_id == getattr(ctx.me, "id", None):
            return

        chat_id = event.chat_id
        now = time.time()

        per_user = st["events"][chat_id][sender_id]
        per_user.append(now)

        while per_user and now - per_user[0] > 5:
            per_user.popleft()

        # One-user burst threshold.
        spam_hit = (
            chat_id in st["spam"]
            and len(per_user) >= 8
        )

        # Distinct-sender burst threshold.
        sender_window = st["events"][chat_id]["__senders__"]
        sender_window.append((now, sender_id))

        while (
            sender_window
            and now - sender_window[0][0] > 15
        ):
            sender_window.popleft()

        distinct_senders = len(
            {item[1] for item in sender_window}
        )

        raid_hit = (
            chat_id in st["raid"]
            and distinct_senders >= 12
        )

        targeted_mute = (
            sender_id in st["targets"]["mute"]
        )

        targeted_lock = (
            sender_id in st["targets"]["lock"]
        )

        chat_muted = chat_id in st["mute_chats"]

        global_dm_mute = (
            event.is_private
            and st["mute_all"]
            and chat_id not in st["unmute"]
        )

        chat_locked = chat_id in st["lock_chats"]

        if (
            spam_hit
            or raid_hit
            or targeted_mute
            o
