"""Encrypted storage for hosted users' sessions (Firestore + Fernet).

Sessions are encrypted with a key that exists only in the VAULT_KEY environment variable, so the
database alone is useless to anyone who reads it. Public hosting stays OFF unless both Firebase and
VAULT_KEY are configured.
"""
import asyncio
import base64
import hashlib
import json
import logging
import struct
import time

from . import config as cfg
from . import db

log = logging.getLogger("runak.vault")


def enabled() -> bool:
    return bool(cfg.VAULT_KEY) and len(cfg.VAULT_KEY) >= 24 and db.client() is not None


def _fernet():
    from cryptography.fernet import Fernet

    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(cfg.VAULT_KEY.encode()).digest()))


def encrypt(obj: dict) -> str:
    return _fernet().encrypt(json.dumps(obj).encode()).decode()


def decrypt(token: str) -> dict:
    return json.loads(_fernet().decrypt(token.encode()).decode())


def pyrogram_string(dc_id: int, api_id: int, auth_key: bytes, user_id: int,
                    test_mode: bool = False, is_bot: bool = False) -> str:
    """Pack an auth key into a Pyrogram v2 session string."""
    raw = struct.pack(">BI?256sQ?", dc_id, api_id, test_mode, auth_key, user_id, is_bot)
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _col():
    return db.client().collection(cfg.VAULT_COLLECTION)


async def save(user_id: int, record: dict) -> None:
    payload = {"blob": encrypt(record), "saved": int(time.time())}
    await asyncio.to_thread(_col().document(str(user_id)).set, payload)


async def delete(user_id: int) -> None:
    await asyncio.to_thread(_col().document(str(user_id)).delete)


async def load_all() -> list[tuple[int, dict]]:
    docs = await asyncio.to_thread(lambda: list(_col().stream()))
    out = []
    for doc in docs:
        try:
            out.append((int(doc.id), decrypt((doc.to_dict() or {})["blob"])))
        except Exception:
            log.error("Could not decrypt vault entry %s (wrong VAULT_KEY?) — leaving it untouched", doc.id)
    return out
