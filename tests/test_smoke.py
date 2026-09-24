"""Offline smoke test: loads every plugin + the panel against fake Telegram objects."""
import asyncio
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["TIMEZONE"] = "Asia/Kolkata"

import fakes  # noqa: E402

httpx = fakes.install()

from runak import config as cfg  # noqa: E402
from runak.branding import BRAND  # noqa: E402
from runak.context import Ctx  # noqa: E402
from runak.plugins import ALL  # noqa: E402
from runak import panel, store as store_mod  # noqa: E402

ME = fakes.User(1, "Owner")
STRANGER = fakes.User(2, "Stranger")
FRIEND = fakes.User(3, "Friend", contact=True)


async def run_command(client, text):
    for builder, fn in client.handlers:
        kw = builder.kw
        if kw.get("outgoing") and re.match(kw["pattern"], text):
            event = fakes.FakeEvent(text, ME)
            event.pattern_match = re.match(kw["pattern"], text)
            await fn(event)
            return " | ".join(event.texts)
    return None  # nothing matched


async def send_dm(client, sender, text="hi"):
    out = []
    for builder, fn in client.handlers:
        if builder.kw.get("incoming"):
            event = fakes.FakeEvent(text, sender)
            await fn(event)
            out += event.texts
    return out


async def main():
    assert cfg.PREFIX == "."
    client, bot = fakes.FakeClient(), fakes.FakeClient()
    st = store_mod.Store()
    await st.load(client)
    ctx = Ctx(client, st, ME)
    ctx.bot = bot
    for m in ALL:
        m.setup(ctx)
        ctx.registry.append(m)
    names = [m.NAME for m in ctx.registry]
    assert "pmguard" not in names, names
    panel.setup(ctx)

    # ---- core / branding
    assert BRAND == "🫧🦋 ʀuɴAk userbot"
    assert BRAND in await run_command(client, ".alive")
    assert BRAND in await run_command(client, ".help")
    assert "Pong" in await run_command(client, ".ping")

    # ---- tools
    assert "60" in await run_command(client, ".calc 12 * (3 + 2)")
    assert "Only basic" in await run_command(client, ".calc __import__('os')")
    assert "𝐡𝐢" in await run_command(client, ".font bold hi")
    pwd = re.search(r"`(.+?)`", await run_command(client, ".pass 20")).group(1)
    assert len(pwd) == 20
    assert "Asia/Tokyo" in await run_command(client, ".time Asia/Tokyo")
    assert "Unknown time zone" in await run_command(client, ".time Mars/Base")

    # ---- notes
    assert "Saved" in await run_command(client, ".save wifi my secret")
    assert "my secret" in await run_command(client, ".get wifi")
    assert "wifi" in await run_command(client, ".notes")
    assert "Deleted" in await run_command(client, ".clear wifi")

    # ---- reminders
    assert "Usage" in await run_command(client, ".remind soon call mom")
    assert "Reminder set" in await run_command(client, ".remind 1h30m call mom")
    assert "call mom" in await run_command(client, ".reminders")
    st.data["reminders"][0]["due"] = time.time() - 1  # make it due
    await asyncio.sleep(15.5)
    assert client.sent and "call mom" in client.sent[-1][1] and client.sent[-1][0] == "me", client.sent
    assert st.data["reminders"] == []

    # ---- AFK: one notice per person
    assert "AFK on" in await run_command(client, ".afk gone fishing")
    first = await send_dm(client, STRANGER)
    assert first and "gone fishing" in first[0]
    assert await send_dm(client, STRANGER) == []
    assert await send_dm(client, fakes.User(9, bot=True)) == []
    await run_command(client, ".unafk")
    assert await send_dm(client, fakes.User(10)) == []

    # ---- AI: off by default, contacts-only scope, needs key
    assert await send_dm(client, FRIEND) == []
    assert "GROQ_API_KEY" in await run_command(client, ".ai on")
    cfg.GROQ_API_KEY = "test-key"
    assert "ON" in await run_command(client, ".ai on")
    assert await send_dm(client, STRANGER, "hello") == []  # not a contact
    assert await send_dm(client, FRIEND, "hello") == ["hello from ai"]
    await run_command(client, ".ai scope everyone")
    assert ctx.store.data["ai"]["scope"] == "everyone"
    await asyncio.sleep(3.1)
    assert await send_dm(client, STRANGER, "hello") == ["hello from ai"]
    assert "hello from ai" in await run_command(client, ".ask what is 2+2")
    assert httpx.calls

    # ---- panel: owner only
    start_handler = next(fn for b, fn in bot.handlers if getattr(b, "kw", {}).get("pattern"))
    cb_handler = next(fn for b, fn in bot.handlers if isinstance(b, sys.modules["telethon"].events.CallbackQuery))

    e = fakes.FakeEvent("/start", STRANGER)
    await start_handler(e)
    assert "private" in e.texts[0]
    e = fakes.FakeEvent("/start", ME)
    await start_handler(e)
    assert BRAND in e.texts[0]

    e = fakes.FakeEvent(sender=STRANGER, data=b"status")
    await cb_handler(e)
    assert e.answers[0][1] is True and not e.texts

    for view in (b"home", b"status", b"plugins", b"ai", b"afk", b"reminders", b"commands", b"about", b"restart"):
        e = fakes.FakeEvent(sender=ME, data=view)
        await cb_handler(e)
        assert e.texts, view
    assert "pmguard" not in e.texts[0].lower()

    # switching a plugin off from the panel really disables its commands
    e = fakes.FakeEvent(sender=ME, data=b"tg:tools")
    await cb_handler(e)
    assert not ctx.enabled("tools")
    for builder, fn in client.handlers:  # calc must now be inert
        if builder.kw.get("outgoing") and re.match(builder.kw["pattern"], ".calc 1+1"):
            ev = fakes.FakeEvent(".calc 1+1", ME)
            ev.pattern_match = re.match(builder.kw["pattern"], ".calc 1+1")
            await fn(ev)
            assert ev.texts == [], "disabled plugin still answered"
    await cb_handler(fakes.FakeEvent(sender=ME, data=b"tg:tools"))
    assert ctx.enabled("tools")
    e = fakes.FakeEvent(sender=ME, data=b"tg:core")
    await cb_handler(e)
    assert ctx.enabled("core")  # core is locked

    # ---- store persistence in Saved Messages
    await asyncio.sleep(2.2)  # debounce
    payloads = [t for _, t in client.sent if t.startswith(store_mod.MARKER)] + [t for _, t in client.edits]
    assert payloads, "settings were never written to Saved Messages"
    saved = payloads[-1]
    c2 = fakes.FakeClient()
    c2.stored = [type("M", (), {"out": True, "raw_text": saved, "id": 7})()]
    s2 = store_mod.Store()
    await s2.load(c2)
    assert s2.data["ai"]["scope"] == "everyone" and s2._msg_id == 7
    s2.data["notes"]["big"] = "x" * 5000
    assert not s2.fits()
    print("smoke OK —", ", ".join(names))


asyncio.run(main())
