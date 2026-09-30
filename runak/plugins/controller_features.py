"""Premium multi-account control features inspired by the supplied controller.

This native plugin ports the controller's target/group/DM rule model into the
current Runak architecture. It also provides working spam/raid *protection*
that detects bursts and removes offending messages when possible.
"""
import asyncio
import time
from collections import defaultdict, deque

from ..context import say

NAME = "controller_features"
TITLE = "⚡ Multi-Account Control"
DESC = "Target rules, group/DM automation, diagnostics, and anti-spam/raid protection."
DEFAULT_ON = True
COMMANDS = [
    ("targetreply", "Auto-reply to a selected user (reply to them or pass @user/id)"),
    ("targetmute", "Delete messages from a selected user"),
    ("targetlock", "Delete and attempt to restrict a selected user"),
    ("replyall", "Toggle rotating group auto-replies"),
    ("mutegc", "Toggle group message deletion"),
    ("lockall", "Toggle group lock/deletion"),
    ("reply", "Toggle rotating DM auto-replies"),
    ("mute", "Toggle current DM mute"),
    ("muteall", "Toggle global DM mute"),
    ("lock", "Toggle current chat lock"),
    ("gcmsgs", "Show the five group reply messages"),
    ("dmmsgs", "Show the five DM reply messages"),
    ("setgc", "Set a group reply: .setgc <1-5> <message>"),
    ("setdm", "Set a DM reply: .setdm <1-5> <message>"),
    ("stopall", "Stop all rules in the current chat"),
    ("status", "Show live rule and protection status"),
    ("spam", "Enable/disable burst spam protection"),
    ("raid", "Enable/disable raid-burst protection"),
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

# In-memory per-client state. Persistent settings live in Store.
STATE = {}


def _state(ctx):
    return STATE.setdefault(id(ctx), {
        "targets": {"reply": set(), "mute": set(), "lock": set()},
        "reply_chats": set(), "mute_chats": set(), "lock_chats": set(),
        "unmute": set(), "mute_all": False,
        "gc": list(GC_DEFAULTS), "dm": list(DM_DEFAULTS),
        "gc_index": defaultdict(int), "dm_index": defaultdict(int),
        "last_reply": {}, "spam": set(), "raid": set(),
        "events": defaultdict(lambda: defaultdict(deque)),
    })


def _persist(ctx, st):
    ctx.store.data.setdefault("controller", {})
    ctx.store.data["controller"] = {
        "targets": {k: list(v) for k, v in st["targets"].items()},
        "reply_chats": list(st["reply_chats"]),
        "mute_chats": list(st["mute_chats"]),
        "lock_chats": list(st["lock_chats"]),
        "unmute": list(st["unmute"]),
        "mute_all": st["mute_all"],
        "gc": st["gc"][:5], "dm": st["dm"][:5],
        "spam": list(st["spam"]), "raid": list(st["raid"]),
    }
    ctx.store.save_soon()


def _load(ctx, st):
    d = ctx.store.data.get("controller", {})
    for k in st["targets"]:
        st["targets"][k].update(int(x) for x in d.get("targets", {}).get(k, []))
    for k in ("reply_chats", "mute_chats", "lock_chats", "unmute", "spam", "raid"):
        st[k].update(int(x) for x in d.get(k, []))
    st["mute_all"] = bool(d.get("mute_all", False))
    if isinstance(d.get("gc"), list) and len(d["gc"]) >= 5:
        st["gc"] = d["gc"][:5]
    if isinstance(d.get("dm"), list) and len(d["dm"]) >= 5:
        st["dm"] = d["dm"][:5]


async def _targets(event, arg):
    found = []
    reply = await event.get_reply_message()
    if reply and getattr(reply, "sender_id", None):
        found.append(reply.sender_id)
    for token in (arg or "").replace(",", " ").split():
        try:
            entity = await event.client.get_entity(int(token) if token.lstrip("-").isdigit() else token)
            uid = getattr(entity, "id", None)
            if uid and uid not in found:
                found.append(uid)
        except Exception:
            continue
    return found


async def _restrict(ctx, event, uid, seconds=600):
    try:
        await event.client.edit_permissions(event.chat_id, uid, send_messages=False, until_date=time.time() + seconds)
        return True
    except Exception:
        return False


def _enabled(st, key, cid):
    if key == "mute_all":
        return st["mute_all"] and cid not in st["unmute"]
    return cid in st[key]


def setup(ctx):
    st = _state(ctx)
    _load(ctx, st)

    @ctx.command(NAME, "target")
    async def target(event, arg):
        parts = (arg or "").split(maxsplit=1)
        if not parts or parts[0].lower() not in {"reply", "mute", "lock"}:
            return await say(event, "Usage: `.target reply|mute|lock @user/id`", md=False)
        kind = parts[0].lower()
        users = await _targets(event, parts[1] if len(parts) > 1 else "")
        if not users:
            return await say(event, "Reply to a user or provide @username/id.", md=False)
        st["targets"][kind].update(users); _persist(ctx, st)
        await say(event, f"✅ Target {kind} enabled for {len(users)} user(s).", md=False)

    @ctx.command(NAME, "stoptarget")
    async def stoptarget(event, arg):
        parts = (arg or "").split(maxsplit=1)
        if not parts or parts[0].lower() not in {"reply", "mute", "lock"}:
            return await say(event, "Usage: `.stoptarget reply|mute|lock @user/id`", md=False)
        kind = parts[0].lower()
        users = await _targets(event, parts[1] if len(parts) > 1 else "")
        if users: st["targets"][kind].difference_update(users)
        else: st["targets"][kind].clear()
        _persist(ctx, st); await say(event, f"✅ Target {kind} stopped.", md=False)

    @ctx.command(NAME, "targetreply")
    async def targetreply(event, arg):
        users = await _targets(event, arg)
        if not users:
            return await say(event, "Usage: reply to a user or use `.targetreply @user`", md=False)
        st["targets"]["reply"].update(users); _persist(ctx, st)
        await say(event, f"✅ Target reply enabled for {len(users)} user(s).", md=False)

    @ctx.command(NAME, "targetmute")
    async def targetmute(event, arg):
        users = await _targets(event, arg)
        if not users:
            return await say(event, "Usage: reply to a user or use `.targetmute @user`", md=False)
        st["targets"]["mute"].update(users); _persist(ctx, st)
        await say(event, f"✅ Target mute enabled for {len(users)} user(s).", md=False)

    @ctx.command(NAME, "targetlock")
    async def targetlock(event, arg):
        users = await _targets(event, arg)
        if not users:
            return await say(event, "Usage: reply to a user or use `.targetlock @user`", md=False)
        st["targets"]["lock"].update(users); _persist(ctx, st)
        await say(event, f"🔒 Target lock enabled for {len(users)} user(s).", md=False)

    @ctx.command(NAME, "stoptargetreply")
    async def stop_target_reply(event, arg):
        users = await _targets(event, arg)
        if users: st["targets"]["reply"].difference_update(users)
        else: st["targets"]["reply"].clear()
        _persist(ctx, st); await say(event, "✅ Target reply stopped.", md=False)

    @ctx.command(NAME, "stoptargetmute")
    async def stop_target_mute(event, arg):
        users = await _targets(event, arg)
        if users: st["targets"]["mute"].difference_update(users)
        else: st["targets"]["mute"].clear()
        _persist(ctx, st); await say(event, "✅ Target mute stopped.", md=False)

    @ctx.command(NAME, "stoptargetlock")
    async def stop_target_lock(event, arg):
        users = await _targets(event, arg)
        if users: st["targets"]["lock"].difference_update(users)
        else: st["targets"]["lock"].clear()
        _persist(ctx, st); await say(event, "✅ Target lock stopped.", md=False)

    @ctx.command(NAME, "replyall")
    async def replyall(event, arg):
        cid = event.chat_id; st["reply_chats"].add(cid); _persist(ctx, st)
        await say(event, "⚡ Group ReplyAll ON — 5-message rotation active.", md=False)

    @ctx.command(NAME, "stopreplyall")
    async def stop_replyall(event, arg):
        st["reply_chats"].discard(event.chat_id); _persist(ctx, st)
        await say(event, "✅ Group ReplyAll OFF.", md=False)

    @ctx.command(NAME, "mutegc")
    async def mutegc(event, arg):
        st["mute_chats"].add(event.chat_id); st["unmute"].discard(event.chat_id); _persist(ctx, st)
        await say(event, "🔇 Group mute protection ON.", md=False)

    @ctx.command(NAME, "stopmutegc")
    async def stop_mutegc(event, arg):
        st["mute_chats"].discard(event.chat_id); st["unmute"].add(event.chat_id); _persist(ctx, st)
        await say(event, "🔊 Group mute protection OFF.", md=False)

    @ctx.command(NAME, "lockall")
    async def lockall(event, arg):
        st["lock_chats"].add(event.chat_id); _persist(ctx, st)
        await say(event, "🔒 Group lock protection ON.", md=False)

    @ctx.command(NAME, "stoplockall")
    async def stop_lockall(event, arg):
        st["lock_chats"].discard(event.chat_id); _persist(ctx, st)
        await say(event, "🔓 Group lock protection OFF.", md=False)

    @ctx.command(NAME, "reply")
    async def reply(event, arg):
        st["reply_chats"].add(event.chat_id); _persist(ctx, st)
        await say(event, "💬 Auto-reply ON — 5-message rotation active.", md=False)

    @ctx.command(NAME, "stopreply")
    async def stop_reply(event, arg):
        st["reply_chats"].discard(event.chat_id); _persist(ctx, st)
        await say(event, "✅ Auto-reply OFF.", md=False)

    @ctx.command(NAME, "mute")
    async def mute(event, arg):
        st["mute_chats"].add(event.chat_id); st["unmute"].discard(event.chat_id); _persist(ctx, st)
        await say(event, "🔇 Mute ON.", md=False)

    @ctx.command(NAME, "stopmute")
    async def stop_mute(event, arg):
        st["mute_chats"].discard(event.chat_id); st["unmute"].add(event.chat_id); _persist(ctx, st)
        await say(event, "🔊 Mute OFF.", md=False)

    @ctx.command(NAME, "muteall")
    async def muteall(event, arg):
        st["mute_all"] = True; _persist(ctx, st)
        await say(event, "🔇 Global DM mute ON. Use `.stopmuteall` to disable.", md=False)

    @ctx.command(NAME, "stopmuteall")
    async def stop_muteall(event, arg):
        st["mute_all"] = False; st["unmute"].clear(); _persist(ctx, st)
        await say(event, "🔊 Global DM mute OFF.", md=False)

    @ctx.command(NAME, "lock")
    async def lock(event, arg):
        st["lock_chats"].add(event.chat_id); _persist(ctx, st)
        await say(event, "🔒 Lock ON.", md=False)

    @ctx.command(NAME, "stoplock")
    async def stop_lock(event, arg):
        st["lock_chats"].discard(event.chat_id); _persist(ctx, st)
        await say(event, "🔓 Lock OFF.", md=False)

    @ctx.command(NAME, "gcmsgs")
    async def gcmsgs(event, arg):
        await say(event, "\n".join(f"{i+1}. {m}" for i, m in enumerate(st["gc"])), md=False)

    @ctx.command(NAME, "dmmsgs")
    async def dmmsgs(event, arg):
        await say(event, "\n".join(f"{i+1}. {m}" for i, m in enumerate(st["dm"])), md=False)

    @ctx.command(NAME, "setgc")
    async def setgc(event, arg):
        p = (arg or "").split(maxsplit=1)
        if len(p) != 2 or not p[0].isdigit() or not 1 <= int(p[0]) <= 5:
            return await say(event, "Usage: `.setgc <1-5> <message>`", md=False)
        st["gc"][int(p[0]) - 1] = p[1]; _persist(ctx, st)
        await say(event, "✅ Group reply updated.", md=False)

    @ctx.command(NAME, "setdm")
    async def setdm(event, arg):
        p = (arg or "").split(maxsplit=1)
        if len(p) != 2 or not p[0].isdigit() or not 1 <= int(p[0]) <= 5:
            return await say(event, "Usage: `.setdm <1-5> <message>`", md=False)
        st["dm"][int(p[0]) - 1] = p[1]; _persist(ctx, st)
        await say(event, "✅ DM reply updated.", md=False)

    @ctx.command(NAME, "stopall")
    async def stopall(event, arg):
        cid = event.chat_id
        for key in ("reply_chats", "mute_chats", "lock_chats", "unmute"):
            st[key].discard(cid)
        for key in st["targets"]:
            st["targets"][key].clear()
        _persist(ctx, st); await say(event, "🛑 All controller rules stopped for this chat.", md=False)

    @ctx.command(NAME, "spam")
    async def spam(event, arg):
        val = (arg or "status").lower()
        if val in ("on", "enable", "1"):
            st["spam"].add(event.chat_id)
        elif val in ("off", "disable", "0"):
            st["spam"].discard(event.chat_id)
        _persist(ctx, st)
        await say(event, f"🛡 Spam protection: {'ON' if event.chat_id in st['spam'] else 'OFF'}", md=False)

    @ctx.command(NAME, "raid")
    async def raid(event, arg):
        val = (arg or "status").lower()
        if val in ("on", "enable", "1"):
            st["raid"].add(event.chat_id)
        elif val in ("off", "disable", "0"):
            st["raid"].discard(event.chat_id)
        _persist(ctx, st)
        await say(event, f"🛡 Raid-burst protection: {'ON' if event.chat_id in st['raid'] else 'OFF'}", md=False)

    @ctx.command(NAME, "status")
    async def status(event, arg):
        cid = event.chat_id
        await say(event, (
            "⚡ CONTROLLER STATUS\n"
            f"Target reply: {'ON' if st['targets']['reply'] else 'OFF'}\n"
            f"Target mute: {'ON' if st['targets']['mute'] else 'OFF'}\n"
            f"Target lock: {'ON' if st['targets']['lock'] else 'OFF'}\n"
            f"ReplyAll: {'ON' if cid in st['reply_chats'] else 'OFF'}\n"
            f"Mute/Lock: {'ON' if cid in st['mute_chats'] else 'OFF'}/{ 'ON' if cid in st['lock_chats'] else 'OFF'}\n"
            f"MuteAll: {'ON' if st['mute_all'] else 'OFF'}\n"
            f"Spam protection: {'ON' if cid in st['spam'] else 'OFF'}\n"
            f"Raid protection: {'ON' if cid in st['raid'] else 'OFF'}"
        ), md=False)

    @ctx.client.on(__import__('telethon').events.NewMessage(incoming=True))
    async def incoming(event):
        if not ctx.enabled(NAME) or event.sender_id in (None, ctx.me.id, 777000):
            return
        cid, uid = event.chat_id, event.sender_id
        now = time.time()
        q = st["events"][cid][uid]
        q.append(now)
        while q and now - q[0] > 5:
            q.popleft()

        # Working burst spam protection: 8+ messages by one user in 5 seconds.
        spam_hit = cid in st["spam"] and len(q) >= 8
        # Working raid-burst protection: 12+ distinct senders in 15 seconds.
        sender_window = st["events"][cid]["__senders__"]
        sender_window.append((now, uid))
        while sender_window and now - sender_window[0][0] > 15:
            sender_window.popleft()
        distinct = len({x[1] for x in sender_window})
        raid_hit = cid in st["raid"] and distinct >= 12

        targeted = uid in st["targets"]["mute"] or uid in st["targets"]["lock"]
        muted = cid in st["mute_chats"] or (event.is_private and st["mute_all"] and cid not in st["unmute"])
        locked = cid in st["lock_chats"]

        if spam_hit or raid_hit or targeted or muted or locked:
            try:
                await event.delete()
            except Exception:
                pass
            if uid in st["targets"]["lock"] or raid_hit:
                await _restrict(ctx, event, uid, 600)
            return

        if uid in st["targets"]["reply"] or ((cid in st["reply_chats"]) and (not event.is_private or event.is_private)):
            # Keep one reply per chat/slot every 2.5 seconds.
            last = st["last_reply"].get(cid, 0)
            if now - last >= 2.5:
                if event.is_private:
                    i = st["dm_index"][cid] % 5; st["dm_index"][cid] += 1; text = st["dm"][i]
                else:
                    i = st["gc_index"][cid] % 5; st["gc_index"][cid] += 1; text = st["gc"][i]
                try:
                    await asyncio.sleep(0.2)
                    await event.reply(text)
                    st["last_reply"][cid] = time.time()
                except Exception:
                    pass
