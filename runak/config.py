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

# ── public hosting (users log in through the bot) — needs Firebase + VAULT_KEY, otherwise it stays off ──
VAULT_KEY = _env("VAULT_KEY")  # secret used to encrypt stored sessions; generate: python -c "import secrets;print(secrets.token_urlsafe(32))"
VAULT_COLLECTION = _env("VAULT_COLLECTION", "runak_vault")
MAX_HOSTED = _int("MAX_HOSTED", 25)  # cap on hosted accounts (each one costs RAM)
HOSTED_LOG_CHAT = _env("HOSTED_LOG_CHAT")  # optional chat id/@username that gets a "New Userbot Hosted" card

GROQ_API_KEY = _env("GROQ_API_KEY")  # optional: only for the AI plugin
GROQ_MODEL = _env("GROQ_MODEL", "llama-3.3-70b-versatile")
DEFAULT_PROMPT = (
    "You are a warm, friendly assistant replying to Telegram direct messages on behalf of "
    "the account owner, who is currently unavailable. Keep replies short and natural. "
    "Never claim to be human. If you don't know something, say so instead of inventing details."
)

# ── /start deployer card (all optional) ──
OWNER_USERNAME = _env("OWNER_USERNAME").lstrip("@")  # shown as the 👑 Owner button, e.g. mybot_owner
UPDATE_URL = _env("UPDATE_URL")  # e.g. https://t.me/your_updates_channel
OPEN_ACCESS = _env("OPEN_ACCESS", "0").lower() in ("1", "true", "yes", "on")  # 1 = anyone may use the bot (no .auth needed)
START_MEDIA = _env("START_MEDIA")  # optional photo/video URL (https) shown on /start

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
