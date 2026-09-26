import random
import time

from telethon.tl.types import DocumentAttributeSticker

from ..context import say

NAME = "sticker"
TITLE = "🎟 Sticker Reply"
DESC = "When an enabled person sends YOU a sticker, reply with a random sticker back (not a text message)."
DEFAULT_ON = True
COMMANDS = [
    ("stickeron", "Reply to someone's message to auto-sticker them"),
    ("stickeroff", "Reply to someone's message to stop"),
    ("stickerpack", "Lock replies to a specific Saved Messages sticker pack"),
]

MAX_TARGETS = 20          # keep the settings message small
CACHE_TTL = 600           # re-scan Saved Messages for stickers every 10 min
SCAN_LIMIT = 500          # how many Saved Messages to look through for stickers


def _is_sticker(msg) -> bool:
    if not msg.sticker:
        return False
    return any(isinstance(a, DocumentAttributeSticker) for a in (msg.sticker.attributes or []))


def _sticker_pack(msg):
    if not msg or not msg.sticker:
        return None
    for attr in (msg.sticker.attributes or []):
        if not isinstance(attr, DocumentAttributeSticker):
            continue
        sticker_set = getattr(attr, "stickerset", None)
        if sticker_set is None:
            return None
        return getattr(sticker_set, "short_name", None) or getattr(sticker_set, "name", None) or getattr(sticker_set, "title", None)
    return None


def setup(ctx):
    targets = lambda: ctx.store.data["sticker"]["targets"]  # noqa: E731
    pack = lambda: ctx.store.data["sticker"].get("pack")  # noqa: E731
    _cache = {}

    async def _saved_stickers(selected_pack=None):
        """Document objects for every sticker found in Saved Messages, optionally filtered to one pack."""
        key = selected_pack or "all"
        entry = _cache.get(key)
        if entry and time.time() - entry["at"] < CACHE_TTL:
            return entry["docs"]

        docs = []
        async for msg in ctx.client.iter_messages("me", limit=SCAN_LIMIT):
            if not _is_sticker(msg):
                continue
            if selected_pack and _sticker_pack(msg) != selected_pack:
                continue
            docs.append(msg.sticker)

        _cache[key] = {"docs": docs, "at": time.time()}
        return docs

    @ctx.command(NAME, "stickerpack")
    async def choose_pack(event, arg):
        arg = (arg or "").strip().lower()
        if arg in {"off", "clear", "reset", "none"}:
            ctx.store.data["sticker"].pop("pack", None)
            ctx.store.save_soon()
            await say(event, "🎟 Auto-sticker uses all saved stickers again.")
            return
        if not event.is_reply:
            await say(event, "🎟 Reply to a sticker from your Saved Messages, then send `.stickerpack` to lock replies to that pack.\nOr send `.stickerpack clear` to reset it.")
            return
        replied = await event.get_reply_message()
        if not _is_sticker(replied):
            await say(event, "❌ Reply to a sticker from your Saved Messages.")
            return
        selected = _sticker_pack(replied)
        if not selected:
            await say(event, "❌ That sticker is not linked to a sticker pack.")
            return
        ctx.store.data["sticker"]["pack"] = selected
        ctx.store.save_soon()
        await say(event, f"🎟 **Sticker pack fixed** to `{selected}`.\nAuto-replies will choose only from that pack.")

    @ctx.command(NAME, "stickeron")
    async def on(event, arg):
        if not event.is_reply:
            await say(event, "🎟 Reply to a message from the person you want to auto-sticker, then send `.stickeron`.")
            return
        replied = await event.get_reply_message()
        sender = await replied.get_sender()
        if not sender or sender.id == ctx.me.id:
            await say(event, "❌ Couldn't find that user.")
            return

        selected_pack = pack()
        docs = await _saved_stickers(selected_pack)
        if not docs and selected_pack:
            docs = await _saved_stickers()
        if not docs:
            await say(event, "❌ No stickers found in your Saved Messages. Save a few stickers there first.")
            return

        t = targets()
        if sender.id not in t and len(t) >= MAX_TARGETS:
            await say(event, f"❌ Limit of {MAX_TARGETS} active targets reached. Turn one off first with `.stickeroff`.")
            return
        if sender.id not in t:
            t.append(sender.id)
            ctx.store.save_soon()

        name = sender.first_name or "this user"
        await say(event, f"🎟 **Sticker auto-reply on** for {name}.\nThey'll get a random saved sticker on every message.")

    @ctx.command(NAME, "stickeroff")
    async def off(event, arg):
        if not event.is_reply:
            await say(event, "🎟 Reply to that person's message, then send `.stickeroff`.")
            return
        replied = await event.get_reply_message()
        sender = await replied.get_sender()
        if not sender:
            await say(event, "❌ Couldn't find that user.")
            return

        t = targets()
        if sender.id not in t:
            await say(event, "It wasn't on for this person.")
            return
        t.remove(sender.id)
        ctx.store.save_soon()
        name = sender.first_name or "this user"
        await say(event, f"🎟 **Sticker auto-reply off** for {name}.")

    @ctx.on_dm(NAME)
    async def auto_reply(event):
        if not _is_sticker(event):
            return  # only stickers get a sticker back; ordinary messages fall through untouched
        sender = await ctx.human_sender(event)
        if not sender or sender.id not in targets():
            return
        selected_pack = pack()
        docs = await _saved_stickers(selected_pack)
        if not docs and selected_pack:
            docs = await _saved_stickers()
        if not docs:
            return
        try:
            await event.reply(file=random.choice(docs))
        except Exception:
            pass
