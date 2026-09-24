"""Tiny stand-ins for telethon/httpx so the whole bot can be smoke-tested offline."""
import contextlib
import sys
import types


class Builder:
    def __init__(self, **kw):
        self.kw = kw


class User:
    def __init__(self, id, first_name="Sam", bot=False, contact=False, deleted=False):
        self.id, self.first_name, self.bot, self.contact, self.deleted = id, first_name, bot, contact, deleted
        self.last_name = None
        self.username = None


def install():
    telethon = types.ModuleType("telethon")
    telethon.__version__ = "fake"
    telethon.events = types.SimpleNamespace(
        NewMessage=type("NewMessage", (Builder,), {}), CallbackQuery=type("CallbackQuery", (Builder,), {})
    )
    telethon.Button = types.SimpleNamespace(inline=lambda text, data: (text, data))
    tl = types.ModuleType("telethon.tl")
    tl_types = types.ModuleType("telethon.tl.types")
    tl_types.User = User
    httpx = types.ModuleType("httpx")
    httpx.calls = []

    class AsyncClient:
        def __init__(self, **kw):
            pass

        async def post(self, url, headers=None, json=None):
            httpx.calls.append(json)

            class R:
                def raise_for_status(self):
                    pass

                def json(self):
                    return {"choices": [{"message": {"content": "hello from ai"}}]}

            return R()

    httpx.AsyncClient = AsyncClient
    sys.modules.update({"telethon": telethon, "telethon.tl": tl, "telethon.tl.types": tl_types, "httpx": httpx})
    return httpx


class FakeClient:
    def __init__(self):
        self.handlers, self.sent, self.edits, self.stored = [], [], [], []

    def on(self, builder):
        def deco(fn):
            self.handlers.append((builder, fn))
            return fn

        return deco

    @contextlib.asynccontextmanager
    async def action(self, *a, **k):
        yield

    async def send_message(self, chat, text, **k):
        self.sent.append((chat, text))
        return types.SimpleNamespace(id=len(self.sent))

    async def edit_message(self, chat, msg_id, text, **k):
        self.edits.append((msg_id, text))

    async def iter_messages(self, *a, **k):
        for m in self.stored:
            yield m

    async def disconnect(self):
        pass


class FakeEvent:
    def __init__(self, text="", sender=None, private=True, data=None, reply=None):
        self.raw_text, self.pattern_match, self.is_private = text, None, private
        self.sender_id = sender.id if sender else None
        self._sender, self._reply = sender, reply
        self.chat_id, self.id, self.data = 1, 100, data
        self.texts, self.answers = [], []

    async def edit(self, text, **k):
        self.texts.append(text)

    async def respond(self, text, **k):
        self.texts.append(text)

    async def answer(self, text=None, alert=False):
        self.answers.append((text, alert))

    async def get_sender(self):
        return self._sender

    async def get_reply_message(self):
        return self._reply
