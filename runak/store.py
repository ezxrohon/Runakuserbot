"""Settings store that survives restarts.

Each account's settings live in one Firestore document, keyed by that account's own
Telegram user id, when Firebase is configured (see `runak/db.py`). Without Firebase
configured, they fall back to one message in that account's own Saved Messages (the old
behaviour) — only that account can read Saved Messages, so it's still private and safe.
An account with an existing Saved Messages store is migrated into Firestore automatically
the first time it connects after Firebase is set up.
"""
import asyncio
import json
import logging

from . import config as cfg
from . import db

log = logging.getLogger("runak.store")

MARKER = "runak-store:v1"  # plain ASCII so Telegram search can always find it
MAX_CHARS = 3800  # a Telegram text message holds 4096 characters — only applies to the fallback


def _defaults() -> dict:
    return {
        "plugins": {},                                   # plugin name -> on/off override
        "afk": {"on": False, "reason": "", "since": 0},
        "ai": {"prompt": None, "scope": "contacts", "smallcaps": True},
        "notes": {},
        "reminders": [],                                 # [{"due": epoch, "text": str}]
        "sticker": {"targets": []},                       # user ids to auto-sticker-reply
    }


class Store:
    def __init__(self, key: str = ""):
        self.key = key  # the account's own Telegram user id, as a string
        self.data = _defaults()
        self._client = None
        self._doc = None
        self._msg_id = None
        self._task = None
        self._dirty = False

    async def load(self, client) -> None:
        self._client = client
        fs = db.client()
        if fs is not None and self.key:
            self._doc = fs.collection(cfg.FIRESTORE_COLLECTION).document(self.key)
            try:
                snap = await asyncio.to_thread(self._doc.get)
                if snap.exists:
                    self._adopt(snap.to_dict() or {})
                    log.info("Settings loaded from Firestore")
                    return
            except Exception:
                log.exception("Could not read Firestore — starting with defaults")
            # No Firestore doc yet: pick up an existing Saved Messages store once, then
            # write it into Firestore so future loads skip this step.
            await self._load_from_saved_messages()
            if self.data != _defaults():
                self.save_soon()
            return
        await self._load_from_saved_messages()

    async def _load_from_saved_messages(self) -> None:
        try:
            for kwargs in ({"search": "runak-store", "limit": 50}, {"limit": 300}):
                async for msg in self._client.iter_messages("me", **kwargs):
                    text = msg.raw_text or ""
                    if msg.out and text.startswith(MARKER):
                        self._adopt(json.loads(text[len(MARKER):].strip() or "{}"))
                        self._msg_id = msg.id
                        log.info("Settings loaded from Saved Messages")
                        return
        except Exception:
            log.warning("Could not load settings from Saved Messages - starting with defaults")

    def _adopt(self, stored: dict) -> None:
        for key, default in _defaults().items():
            value = stored.get(key, default)
            if isinstance(default, dict) and isinstance(value, dict):
                merged = dict(default)
                merged.update(value)
                value = merged
            self.data[key] = value

    def size(self) -> int:
        return len(json.dumps(self.data, ensure_ascii=False, separators=(",", ":")))

    def fits(self) -> bool:
        """Only meaningful for the Saved-Messages fallback; Firestore has far more room."""
        return self._doc is not None or self.size() <= MAX_CHARS - len(MARKER)

    def save_soon(self) -> None:
        """Mark dirty and write shortly after (debounced, so bursts become one write)."""
        self._dirty = True
        if self._client and (self._task is None or self._task.done()):
            self._task = asyncio.get_running_loop().create_task(self._debounced())

    async def _debounced(self) -> None:
        await asyncio.sleep(2)
        await self.flush()

    async def flush(self) -> None:
        if not self._client or not self._dirty:
            return
        self._dirty = False
        if self._doc is not None:
            try:
                await asyncio.to_thread(self._doc.set, self.data)
            except Exception:
                log.exception("Saving settings to Firestore failed")
                self._dirty = True
            return
        await self._flush_to_saved_messages()

    async def _flush_to_saved_messages(self) -> None:
        payload = MARKER + "\n" + json.dumps(self.data, ensure_ascii=False, separators=(",", ":"))
        if len(payload) > MAX_CHARS:
            log.warning("Settings are too large to save (%d chars) - delete some notes", len(payload))
            return
        for attempt in (1, 2):
            try:
                if self._msg_id:
                    await self._client.edit_message("me", self._msg_id, payload, parse_mode=None)
                else:
                    msg = await self._client.send_message("me", payload, parse_mode=None, silent=True)
                    self._msg_id = msg.id
                return
            except Exception as exc:
                if "not modified" in str(exc).lower():
                    return
                log.warning("Saving settings failed (%s), attempt %d", type(exc).__name__, attempt)
                self._msg_id = None  # message may have been deleted: create a fresh one
