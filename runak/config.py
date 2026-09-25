"""Configuration from environment variables.

There are NO built-in secrets, API keys or default admin IDs in this project.
"""
import os
import re


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _int(name: str, default: int = 0) -> int:
    try:
        return int(_env(name) or default)
    except ValueError:
        return default


def _prefix() -> str:
    value = _env("PREFIX", ".")
    return value if 1 <= len(value) <= 3 and not any(c.isspace() for c in value) else "."


def _sessions() -> list[str]:
    """One or more Telethon session strings — one per Telegram account you own.

    `TELEGRAM_SESSIONS` takes a comma- or newline-separated list for multiple accounts.
    `TELEGRAM_SESSION` (singular, from create_session.py) still works for one account and
    is folded in too, so existing single-account setups need no changes.
    """
    raw = _env("TELEGRAM_SESSIONS")
    parts = [p.strip() for p in re.split(r"[,\n]+", raw) if p.strip()] if raw else []
    single = _env("TELEGRAM_SESSION") or _env("STRING_SESSION")
    if single and single not in parts:
        parts.append(single)
    return parts


API_ID = _int("API_ID")
API_HASH = _env("API_HASH")
SESSIONS = _sessions()  # one Telethon session string per account, all owned by the same person
BOT_TOKEN = _env("BOT_TOKEN")  # optional: without it the userbot runs with no panel
OWNER_ID = _int("OWNER_ID") or None  # optional: extra Telegram user ID allowed to use the panel

# ── storage: Firestore is used when credentials are present, otherwise each account falls
# back to saving its own settings in its own Saved Messages (old behaviour, zero setup). ──
FIREBASE_CREDENTIALS_JSON = _env("FIREBASE_CREDENTIALS_JSON")  # paste the service-account JSON, one line
GOOGLE_APPLICATION_CREDENTIALS = _env("GOOGLE_APPLICATION_CREDENTIALS")  # or a path to that JSON file
FIRESTORE_COLLECTION = _env("FIRESTORE_COLLECTION", "runak_accounts")

GROQ_API_KEY = _env("GROQ_API_KEY")  # optional: only for the AI plugin
GROQ_MODEL = _env("GROQ_MODEL", "llama-3.3-70b-versatile")
DEFAULT_PROMPT = (
    "You are a warm, friendly assistant replying to Telegram direct messages on behalf of "
    "the account owner, who is currently unavailable. Keep replies short and natural. "
    "Never claim to be human. If you don't know something, say so instead of inventing details."
)

PREFIX = _prefix()
TIMEZONE = _env("TIMEZONE", "UTC")

PORT = _int("PORT", 10000)
EXTERNAL_URL = _env("RENDER_EXTERNAL_URL") or _env("EXTERNAL_URL")
KEEPALIVE = _env("KEEPALIVE", "1").lower() not in ("0", "false", "no", "off")


def missing_required() -> list[str]:
    missing = []
    if not API_ID:
        missing.append("API_ID")
    if not API_HASH:
        missing.append("API_HASH")
    if not SESSIONS:
        missing.append("TELEGRAM_SESSION(S)")
    return missing
