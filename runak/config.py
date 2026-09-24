"""Configuration from environment variables.

There are NO built-in secrets, API keys or default admin IDs in this project.
"""
import os


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


API_ID = _int("API_ID")
API_HASH = _env("API_HASH")
SESSION = _env("TELEGRAM_SESSION") or _env("STRING_SESSION")
BOT_TOKEN = _env("BOT_TOKEN")  # optional: without it the userbot runs with no panel

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
    if not SESSION:
        missing.append("TELEGRAM_SESSION")
    return missing
