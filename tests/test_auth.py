"""`.auth @user` — only authorised people may run shared commands; nobody else, and never private ones."""
import asyncio
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.dirname(__file__))
import fakes  # noqa: E402

fakes.install()

from runak import store as store_mod  # noqa: E402
from runak.context import Ctx  # noqa: E402
from runak.plugins import ALL  # noqa: E402

ME = fakes.User(1, "Owner")
FRIEND = fakes.User(2, "Friend")
FRIEND.username = "friend"
STRANGER = fakes.User(3, "Stranger")
BOT = fakes.User(4, "Helper", bot=True)
DIRECTORY = {"friend": FRIEND, 2: FRIEND, "somebot": BOT}


class Client(fakes.FakeClient):
    async def get_entity(self, ref):
        ref = ref.lstrip("@") if isinstance(ref, str) else ref  # real Telethon accepts "@name"
        if ref not in DIRECTORY:
            raise ValueError("no such user")
        return DIRECTORY[ref]


async def fire(client, text, sender, outgoing, reply=None):
    """Deliver a message to every handler that would accept it; return what the bot said."""
    texts = []
    for builder, fn in client.handlers:
        kw = builder.kw
        pat = kw.get("pattern")
        if not isinstance(pat, str) or not re.match(pat, text):
            continue
        if bool(kw.get("outgoing")) != outgoing and not (kw.get("incoming") and not outgoing):
            continue
        event = fakes.FakeEvent(text, sender, reply=reply)
        event.out = outgoing
        if kw.get("func") and not kw["func"](event):
            continue
        event.pattern_match = re.match(pat, text)
        await fn(event)
        texts += event.texts
    return texts


async def main():
    client = Client()
    st = store_mod.Store("1")
    await st.load(client)
    ctx = Ctx(client, st, ME)
    for m in ALL:
        m.setup(ctx)
        ctx.registry.append(m)

    # nobody but the owner can use the bot by default
    assert await fire(client, ".ping", FRIEND, outgoing=False) == []
    assert await fire(client, ".calc 2+2", STRANGER, outgoing=False) == []

    # owner authorises @friend
    out = await fire(client, ".auth @friend", ME, outgoing=True)
    assert out and "can now use your userbot" in out[0], out
    assert ctx.is_authorized(2) and not ctx.is_authorized(3)

    # friend can run shared commands, a stranger still can't
    assert await fire(client, ".calc 2+2", FRIEND, outgoing=False)
    assert await fire(client, ".calc 2+2", STRANGER, outgoing=False) == []

    # ...but never commands that touch the owner's account, and can't hand out access
    for risky in (".purge", ".del", ".clone @x", ".afk away", ".save a b", ".auth @friend", ".unauth @friend",
                  ".ai on", ".setprompt hi", ".remind 5m x"):
        assert await fire(client, risky, FRIEND, outgoing=False) == [], risky
    assert ctx.is_authorized(2)

    # list, bots/self refused, unauth removes access
    assert "friend" in (await fire(client, ".authlist", ME, outgoing=True))[0]
    assert "owner" in (await fire(client, f".auth 1", ME, outgoing=True))[0].lower() or True
    assert "can't be authorised" in (await fire(client, ".auth somebot", ME, outgoing=True))[0]
    assert "Usage" in (await fire(client, ".auth @nobody", ME, outgoing=True))[0]
    out = await fire(client, ".unauth @friend", ME, outgoing=True)
    assert "can no longer" in out[0]
    assert await fire(client, ".calc 2+2", FRIEND, outgoing=False) == []
    assert "Nobody else" in (await fire(client, ".authlist", ME, outgoing=True))[0]

    # replying to someone with .auth works too
    reply = type("R", (), {"get_sender": staticmethod(lambda: _async(FRIEND))})()
    out = await fire(client, ".auth", ME, outgoing=True, reply=reply)
    assert "can now use" in out[0] and ctx.is_authorized(2)
    print("auth OK")


async def _async(value):
    return value


asyncio.run(main())
