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
    telethon.Button = types.SimpleNamespace(inline=lambda text, data: (text, data), url=lambda text, url: (text, url))
    class TelegramClient:  # replaced by tests that exercise the login flow
        def __init__(self, *a, **k):
            pass

    telethon.TelegramClient = TelegramClient
    sessions = types.ModuleType("telethon.sessions")
    sessions.StringSession = lambda s=None: s
    errors = types.ModuleType("telethon.errors")
    for name in ("FloodWaitError", "PasswordHashInvalidError", "PhoneCodeExpiredError", "PhoneCodeInvalidError",
                 "PhoneNumberInvalidError", "SessionPasswordNeededError"):
        setattr(errors, name, type(name, (Exception,), {}))
    tl = types.ModuleType("telethon.tl")
    tl_types = types.ModuleType("telethon.tl.types")
    tl_types.User = User
    class Channel: pass
    class Chat: pass
    tl_types.Channel = Channel
    tl_types.Chat = Chat

    class DocumentAttributeSticker:
        pass

    tl_types.DocumentAttributeSticker = DocumentAttributeSticker

    # Minimal TL stubs used by optional plugins during import.  The smoke suite
    # does not execute these network operations, but importing every plugin
    # should still work offline.
    tl_functions = types.ModuleType("telethon.tl.functions")
    tl_functions_users = types.ModuleType("telethon.tl.functions.users")
    tl_functions_photos = types.ModuleType("telethon.tl.functions.photos")
    tl_functions_account = types.ModuleType("telethon.tl.functions.account")
    tl_functions_messages = types.ModuleType("telethon.tl.functions.messages")

    class _Request:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    tl_functions_users.GetFullUserRequest = _Request
    tl_functions_photos.UploadProfilePhotoRequest = _Request
    tl_functions_account.UpdateProfileRequest = _Request
    tl_functions_messages.SendReactionRequest = _Request
    tl_functions_auth = types.ModuleType("telethon.tl.functions.auth")
    tl_functions_auth.AcceptLoginTokenRequest = _Request
    tl_functions_account.GetAuthorizationsRequest = _Request
    tl_functions_account.ResetAuthorizationRequest = _Request
    tl_functions.auth = tl_functions_auth
    tl_functions.users = tl_functions_users
    tl_functions.photos = tl_functions_photos
    tl_functions.account = tl_functions_account
    tl_functions.messages = tl_functions_messages

    class ReactionEmoji:
        def __init__(self, emoticon=None):
            self.emoticon = emoticon

    tl_types.ReactionEmoji = ReactionEmoji
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
    sys.modules.update({
        "telethon": telethon,
        "telethon.sessions": sessions,
        "telethon.errors": errors,
        "telethon.tl": tl,
        "telethon.tl.types": tl_types,
        "telethon.tl.functions": tl_functions,
        "telethon.tl.functions.users": tl_functions_users,
        "telethon.tl.functions.photos": tl_functions_photos,
        "telethon.tl.functions.account": tl_functions_account,
        "telethon.tl.functions.messages": tl_functions_messages,
        "telethon.tl.functions.auth": tl_functions_auth,
        "httpx": httpx,
    })
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
        self.sticker = None
        self.is_reply = reply is not None

    async def edit(self, text, **k):
        self.texts.append(text)

    async def respond(self, text, **k):
        self.texts.append(text)

    async def answer(self, text=None, alert=False):
        self.answers.append((text, alert))

    async def get_sender(self):
        return self._sender

    async def delete(self):
        self.deleted = True

    async def get_reply_message(self):
        return self._reply
