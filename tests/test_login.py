"""Offline tests for the login flow, vault encryption and Pyrogram string packing."""
import asyncio
import base64
import os
import struct
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["VAULT_KEY"] = "k" * 40

import fakes  # noqa: E402

fakes.install()

from runak import config as cfg  # noqa: E402
from runak import access, login, vault  # noqa: E402

access.allowed = lambda uid: uid != 99  # 99 plays an unauthorised stranger

errors = sys.modules["telethon.errors"]
STORE = {}


class FakeSession:
    dc_id = 2
    auth_key = types.SimpleNamespace(key=b"\x07" * 256)

    def save(self):
        return "TG-STRING"


class FakeTG:
    needs_2fa = False
    instances = []

    def __init__(self, *a, **k):
        self.session, self.calls = FakeSession(), []
        FakeTG.instances.append(self)

    async def connect(self): pass
    async def disconnect(self): pass

    async def send_code_request(self, phone):
        return types.SimpleNamespace(phone_code_hash="H")

    async def sign_in(self, phone=None, code=None, phone_code_hash=None, password=None):
        if password is None and FakeTG.needs_2fa:
            raise errors.SessionPasswordNeededError()
        if code and code != "12345":
            raise errors.PhoneCodeInvalidError()

    async def get_me(self):
        return types.SimpleNamespace(id=555, first_name="Asha")


async def fake_second(client, me, password):
    return "PYRO", "HASH"


class FakeCtx:
    tasks = []
    bot = None

    class client:
        @staticmethod
        async def run_until_disconnected(): await asyncio.sleep(0)
        @staticmethod
        async def log_out(): STORE["logged_out"] = True
        @staticmethod
        async def disconnect(): pass
        @staticmethod
        async def __call__(*a, **k): pass


async def start_account(session, idx):
    return FakeCtx() if session == "TG-STRING" else None


class Bot(fakes.FakeClient):
    pass


def ev(text, uid, data=None):
    e = fakes.FakeEvent(text, fakes.User(uid), data=data)
    return e


async def main():
    # pyrogram string packs to the documented v2 layout
    packed = vault.pyrogram_string(2, 12345, b"\x07" * 256, 555)
    raw = base64.urlsafe_b64decode(packed + "=" * (-len(packed) % 4))
    assert struct.unpack(">BI?256sQ?", raw) == (2, 12345, False, b"\x07" * 256, 555, False)

    # vault round-trips and the ciphertext hides the session
    blob = vault.encrypt({"tg": "SECRET-SESSION"})
    assert "SECRET-SESSION" not in blob and vault.decrypt(blob) == {"tg": "SECRET-SESSION"}

    # login flow
    login.TelegramClient = FakeTG
    login.second_session = fake_second
    vault.enabled = lambda: True
    async def save(uid, rec): STORE["saved"] = (uid, rec)
    vault.save = save
    cfg.API_ID = 1
    bot, hosted, tasks = Bot(), {}, set()
    login.setup(bot, start_account, hosted, tasks)
    by_pattern = lambda text: next(fn for b, fn in bot.handlers if isinstance(b.kw.get("pattern"), str) and __import__("re").match(b.kw["pattern"], text))
    cb = next(fn for b, fn in bot.handlers if isinstance(b.kw.get("pattern"), bytes))
    flow_in = next(fn for b, fn in bot.handlers if b.kw.get("pattern") is None)

    e = ev("/login", 7); await by_pattern("/login")(e)
    assert "I agree" not in e.texts[0] and "Login" in e.texts[0]
    e = ev("", 7, b"lg:agree"); await cb(e)
    assert "phone" in e.texts[0]
    flow_in.__globals__  # handler registered with a func filter; call it directly
    e = ev("+91 12345 67890", 7); await flow_in(e)
    assert "spaces" in e.texts[0]
    e = ev("9 9 9 9 9", 7); await flow_in(e)
    assert "Wrong" in e.texts[0]
    e = ev("1 2 3 4 5", 7); await flow_in(e)
    assert "hosted" in e.texts[0] and "Pyrogram ✅" in e.texts[0], e.texts
    assert STORE["saved"][0] == 555 and STORE["saved"][1]["pyro"] == "PYRO"
    assert 555 in hosted

    # already hosted -> no second login; logout removes + deletes
    e = ev("/login", 555); await by_pattern("/login")(e)
    assert "already" in e.texts[0]
    async def delete(uid): STORE["deleted"] = uid
    async def load_all(): return [(555, {"pyro_hash": "HASH"})]
    vault.delete, vault.load_all = delete, load_all
    e = ev("", 555, b"lg:logout:yes"); await cb(e)
    assert STORE.get("deleted") == 555 and STORE.get("logged_out") and 555 not in hosted

    # unauthorised people get the card, not the consent screen
    e = ev("/login", 99); await by_pattern("/login")(e)
    assert "NOT AUTHORIZED" in e.texts[0]
    e = ev("", 99, b"lg:agree"); await cb(e)
    assert e.answers and e.answers[0][1] is True

    # vault off -> login refused
    vault.enabled = lambda: False
    e = ev("/login", 8); await by_pattern("/login")(e)
    assert "isn't enabled" in e.texts[0]
    print("login OK")


asyncio.run(main())
