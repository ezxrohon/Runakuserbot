"""Create your TELEGRAM_SESSION string. Run this on YOUR OWN computer, never on a server
and never through someone else's "session bot".

    pip install telethon
    python create_session.py
"""
import os

from telethon import TelegramClient
from telethon.sessions import StringSession

api_id = int(os.getenv("API_ID") or input("API_ID (from my.telegram.org): ").strip())
api_hash = os.getenv("API_HASH") or input("API_HASH: ").strip()

with TelegramClient(StringSession(), api_id, api_hash) as tg:
    print("\nYour TELEGRAM_SESSION (treat it like a password — anyone with it controls your account):\n")
    print(tg.session.save())
    print()
