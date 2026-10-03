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
from runak.helpers import small_caps  # noqa: E402
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


async def send_dm(client, sender, text="hi", sticker=None):
    out = []
    for builder, fn in client.handlers:
        if builder.kw.get("incoming"):
            if builder.kw.get("pattern") and not re.match(builder.kw["pattern"], text):
                continue
            event = fakes.FakeEvent(text, sender)
            event.sticker = sticker
            await fn(event)
            out += event.texts
    return out


async def main():
    assert cfg.PREFIX == "."
    client, bot = fakes.FakeClient(), fakes.FakeClient()
    st = store_mod.Store(str(ME.id))
    await st.load(client)
    ctx = Ctx(client, st, ME)
    for m in ALL:
        m.setup(ctx)
        ctx.registry.append(m)
    names = [m.NAME for m in ctx.registry]
    assert "pmguard" not in names, names
    ctx.bot = bot
    panel.setup(bot, [ctx])

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

    # ---- sticker reply: only fires when the incoming message IS a sticker, for enabled targets
    assert await send_dm(client, STRANGER, text="hi") == []  # target not enabled, and not a sticker either

    # ---- AI: off by default, contacts-only scope, needs key
    assert await send_dm(client, FRIEND) == []
    assert "GROQ_API_KEY" in await run_command(client, ".ai on")
    cfg.GROQ_API_KEY = "test-key"
    assert "ON" in await run_command(client, ".ai on")
    assert await send_dm(client, STRANGER, "hello") == []  # not a contact
    assert await send_dm(client, FRIEND, "hello") == [small_caps("hello from ai")]
    await run_command(client, ".ai scope everyone")
    assert ctx.store.data["ai"]["scope"] == "everyone"
    await asyncio.sleep(3.1)
    assert await send_dm(client, STRANGER, "hello") == [small_caps("hello from ai")]
    assert small_caps("hello from ai") in await run_command(client, ".ask what is 2+2")
    assert httpx.calls
    assert "OFF" in await run_command(client, ".ai smallcaps off")
    await asyncio.sleep(3.1)
    assert await send_dm(client, STRANGER, "hello") == ["hello from ai"]  # no longer small-capped

    # ---- panel: /start is public (deployer card); /panel is owner only
    def handler_for(text):
        return next(fn for b, fn in bot.handlers
                    if isinstance(getattr(b, "kw", {}).get("pattern"), str) and re.match(b.kw["pattern"], text))

    cb_handler = next(fn for b, fn in bot.handlers
                      if isinstance(b, sys.modules["telethon"].events.CallbackQuery)
                      and not (b.kw.get("pattern") or b"").startswith(b"^(hm|st)"))
    pub_cb = next(fn for b, fn in bot.handlers
                  if isinstance(b, sys.modules["telethon"].events.CallbackQuery)
                  and (b.kw.get("pattern") or b"").startswith(b"^(hm|st)"))

    # not authorised yet: /start, /help and the buttons all refuse
    e = fakes.FakeEvent("/start", STRANGER)
    await handler_for("/start")(e)
    assert "NOT AUTHORIZED" in e.texts[0] and ".auth @yourusername" in e.texts[0]
    e = fakes.FakeEvent("/help", STRANGER)
    await handler_for("/help")(e)
    assert "NOT AUTHORIZED" in e.texts[0]
    e = fakes.FakeEvent(sender=STRANGER, data=b"hm:p:0")
    await pub_cb(e)
    assert e.answers[0][1] is True and not e.texts
    # an admin runs `.auth` for them -> they're in
    ctx.store.data["auth"]["users"][str(STRANGER.id)] = "stranger"
    e = fakes.FakeEvent("/start", STRANGER)
    await handler_for("/start")(e)
    assert "RUNAK USERBOT DEPLOYER" in e.texts[0]
    e = fakes.FakeEvent("/panel", STRANGER)
    await handler_for("/panel")(e)
    assert "private" in e.texts[0]
    e = fakes.FakeEvent("/panel", ME)
    await handler_for("/panel")(e)
    assert BRAND in e.texts[0]  # single account: /panel opens the account's home directly

    # ---- help menu: open to everyone, paged, every category renders
    from runak import helpmenu
    e = fakes.FakeEvent("/help", STRANGER)
    await handler_for("/help")(e)
    assert "Help Menu" in e.texts[0]
    for page in range(helpmenu.page_count()):
        e = fakes.FakeEvent(sender=STRANGER, data=f"hm:p:{page}".encode())
        await pub_cb(e)
        assert "Help Menu" in e.texts[0] and not e.answers[0][1], page
    for key, _label, _plugins in helpmenu.CATEGORIES:
        e = fakes.FakeEvent(sender=STRANGER, data=f"hm:c:{key}:0".encode())
        await pub_cb(e)
        assert e.texts, key
    e = fakes.FakeEvent(sender=STRANGER, data=b"hm:c:afk:0")
    await pub_cb(e)
    assert ".afk" in e.texts[0]
    e = fakes.FakeEvent(sender=STRANGER, data=b"hm:c:musicvc:0")
    await pub_cb(e)
    assert "Coming soon" in e.texts[0]
    e = fakes.FakeEvent(sender=STRANGER, data=b"hm:x")
    await pub_cb(e)
    assert getattr(e, "deleted", False)
    # deployer buttons: Login is handled by login.py (open to everyone); control panel is owner-only
    e = fakes.FakeEvent(sender=STRANGER, data=b"st:login")
    await pub_cb(e)
    assert not e.answers and not e.texts
    e = fakes.FakeEvent(sender=STRANGER, data=b"st:panel")
    await pub_cb(e)
    assert e.answers[0][1] is True and not e.texts
    e = fakes.FakeEvent(sender=ME, data=b"st:panel")
    await pub_cb(e)
    assert BRAND in e.texts[0]
    # the owner-panel handler ignores public prefixes instead of rejecting them
    e = fakes.FakeEvent(sender=STRANGER, data=b"hm:p:0")
    await cb_handler(e)
    assert not e.answers

    e = fakes.FakeEvent(sender=STRANGER, data=b"a:0:status")
    await cb_handler(e)
    assert e.answers[0][1] is True and not e.texts

    for view in (b"a:0:home", b"a:0:status", b"a:0:plugins", b"a:0:ai", b"a:0:afk",
                 b"a:0:reminders", b"a:0:commands", b"a:0:about", b"a:0:restart"):
        e = fakes.FakeEvent(sender=ME, data=view)
        await cb_handler(e)
        assert e.texts, view
    assert "pmguard" not in e.texts[0].lower()

    # switching a plugin off from the panel really disables its commands
    e = fakes.FakeEvent(sender=ME, data=b"a:0:tg:tools")
    await cb_handler(e)
    assert not ctx.enabled("tools")
    for builder, fn in client.handlers:  # calc must now be inert
        if builder.kw.get("outgoing") and re.match(builder.kw["pattern"], ".calc 1+1"):
            ev = fakes.FakeEvent(".calc 1+1", ME)
            ev.pattern_match = re.match(builder.kw["pattern"], ".calc 1+1")
            await fn(ev)
            assert ev.texts == [], "disabled plugin still answered"
    await cb_handler(fakes.FakeEvent(sender=ME, data=b"a:0:tg:tools"))
    assert ctx.enabled("tools")
    e = fakes.FakeEvent(sender=ME, data=b"a:0:tg:core")
    await cb_handler(e)
    assert ctx.enabled("core")  # core is locked

    # ---- store persistence in Saved Messages (no Firebase configured in this test)
    await asyncio.sleep(2.2)  # debounce
    payloads = [t for _, t in client.sent if t.startswith(store_mod.MARKER)] + [t for _, t in client.edits]
    assert payloads, "settings were never written to Saved Messages"
    saved = payloads[-1]
    c2 = fakes.FakeClient()
    c2.stored = [type("M", (), {"out": True, "raw_text": saved, "id": 7})()]
    s2 = store_mod.Store(str(ME.id))
    await s2.load(c2)
    assert s2.data["ai"]["scope"] == "everyone" and s2._msg_id == 7
    s2.data["notes"]["big"] = "x" * 5000
    assert not s2.fits()
    print("smoke OK —", ", ".join(names))


asyncio.run(main())
