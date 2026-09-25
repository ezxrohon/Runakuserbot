"""Optional Firestore connection, shared by every account's Store.

Nothing here is required: if no Firebase credentials are configured, `client()` returns
None and each account's Store falls back to saving settings in its own Saved Messages,
exactly like before.
"""
import json
import logging

from . import config as cfg

log = logging.getLogger("runak.db")

_client = None
_tried = False


def configured() -> bool:
    return bool(cfg.FIREBASE_CREDENTIALS_JSON or cfg.GOOGLE_APPLICATION_CREDENTIALS)


def client():
    """Return a cached Firestore client, or None if Firebase isn't configured/available."""
    global _client, _tried
    if _client is not None or _tried:
        return _client
    _tried = True
    if not configured():
        return None
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if firebase_admin._apps:
            app = firebase_admin.get_app()
        elif cfg.FIREBASE_CREDENTIALS_JSON:
            app = firebase_admin.initialize_app(credentials.Certificate(json.loads(cfg.FIREBASE_CREDENTIALS_JSON)))
        else:
            app = firebase_admin.initialize_app(credentials.Certificate(cfg.GOOGLE_APPLICATION_CREDENTIALS))
        _client = firestore.client(app)
        log.info("Connected to Firestore")
    except Exception:
        log.exception("Firebase/Firestore init failed — falling back to Saved Messages storage")
        _client = None
    return _client
