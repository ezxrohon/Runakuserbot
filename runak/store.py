"""Settings store that survives Render's ephemeral disk.

Render free web services lose their local files on every restart and spin-down, so the
settings live in ONE message in your own Saved Messages (it starts with the marker below).
Please don't delete that message. Only your account can read Saved Messages.
"""
import asyncio
import json
import logging

log = logging.getLogger("runak.store")

MARKER = "runak-store:v1"  # plain ASCII so Telegram search can always find it
MAX_CHARS = 3800  # a Telegram text message holds 4096 characters


def _defaults() -> dict:
    return {
        "plugins": {},                                   # plugin name -> on/off override
        "afk": {"on": False, "reason": "", "since": 0},
        "ai": {"prompt": None, "scope": "contacts"},
        "notes": {},
        "reminders": [],                                 # [{"due": epoch, "text": str}]
    }


class Store:
    def __init__(self):
        self.data = _defaults()
        self._client = None
        self._msg_id = None
        self._task = None
        self._dirty = False

    async def load(self, client) -> None:
        self._client = client
        try:
            # Fast path: Telegram search. Fallback: scan the latest Saved Messages.
            for kwargs in ({"search": "runak-store", "limit": 50}, {"limit": 300}):
                async for msg in client.iter_messages("me", **kwargs):
                    text = msg.raw_text or ""
                    if msg.out and text.startswith(MARKER):
                        self._adopt(json.loads(text[len(MARKER):].strip() or "{}"))
                        self._msg_id = msg.id
                        log.info("Settings loaded from Saved Messages")
                        return
        except Exception as exc:
            log.warning("Could not load settings (%s) - starting with defaults", type(exc).__name__)

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
        return self.size() <= MAX_CHARS - len(MARKER)

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
