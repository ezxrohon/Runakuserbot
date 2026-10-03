"""Paged, button-driven help menu + the /start "deployer" card.

Layout mirrors a classic userbot help screen: a 2-column grid of category buttons, Prev/Next page
buttons and a Close button. Each category is backed by one or more real plugins, so the command list
shown is always generated from the plugin's own COMMANDS — it can never drift out of date. A category
with no plugin yet is listed as "coming soon" so the grid layout stays stable as features are added.
"""
from telethon import Button

from . import config as cfg
from .branding import BRAND, DEPLOYER_CAPABILITIES, DEPLOYER_STEPS, DEPLOYER_TITLE
from .plugins import ALL

PAGE_SIZE = 10  # 5 rows x 2 columns per page

# (key, button label, [plugin NAMEs]).  Empty plugin list = not built yet.
CATEGORIES = [
    ("tagall", "📣 Tagall", ["tagall", "all_tag"]),
    ("locks", "🔒 Locks", []),
    ("admin", "🛡 Admin", []),
    ("sticker", "🎨 Sticker", ["sticker"]),
    ("groupinfo", "📊 Group Info", []),
    ("spam", "🚀 Spam", ["spam"]),
    ("clone", "👤 Clone Profile", ["clone"]),
    ("dmsecurity", "🔐 DM Security", []),
    ("musicvc", "🎵 Music VC", []),
    ("afk", "💤 AFK Status", ["afk"]),
    ("vctools", "🎙 VC Tools", []),
    ("vcfight", "⚔️ VC Fight", []),
    ("chathelpers", "💬 Chat Helpers", ["core", "auth", "purge", "remind"]),
    ("jokes", "🤣 Jokes & Quotes", ["shayari", "memestext", "love"]),
    ("typing", "⌨️ Typing Anims", ["animation", "animation1", "animation4", "animation5"]),
    ("ascii", "🖼 ASCII & Figlet", ["arts", "funarts", "emojify"]),
    ("zombies", "🧟 Zombies", []),
    ("wordseek", "🔠 WordSeek", []),
    ("appstore", "📱 App Store", ["playstore"]),
    ("anime", "⛩ Anime Search", []),
    ("pets", "🐶 Pets & Waifu", []),
    ("zip", "📦 Zip & Archive", []),
    ("echo", "🔁 Echo Repeater", []),
    ("notes", "📝 Chat Notes", ["notes"]),
    ("hash", "🔐 Hash & Base64", ["tools"]),
]
_BY_KEY = {key: (label, plugins) for key, label, plugins in CATEGORIES}
_PLUGINS = {m.NAME: m for m in ALL}


def page_count() -> int:
    return max(1, (len(CATEGORIES) + PAGE_SIZE - 1) // PAGE_SIZE)


def help_page(page: int = 0):
    """Return (text, buttons) for one page of the category grid."""
    page = max(0, min(int(page), page_count() - 1))
    chunk = CATEGORIES[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]
    cells = [Button.inline(label, f"hm:c:{key}:{page}".encode()) for key, label, _ in chunk]
    rows = [cells[n:n + 2] for n in range(0, len(cells), 2)]
    nav = []
    if page > 0:
        nav.append(Button.inline(f"◀️ Prev (Page {page}/{page_count()})", f"hm:p:{page - 1}".encode()))
    nav.append(Button.inline("❌ Close ❌", b"hm:x"))
    if page + 1 < page_count():
        nav.append(Button.inline(f"Next ▶️ (Page {page + 2}/{page_count()})", f"hm:p:{page + 1}".encode()))
    rows.append(nav)
    text = (
        f"⚙️ **{BRAND} Help Menu** ⚙️\n\n"
        f"**Select a category below to view available commands:**"
    )
    return text, rows


def category_page(key: str, page: int = 0):
    """Return (text, buttons) for one category's command list."""
    if key not in _BY_KEY:
        return help_page(page)
    label, plugin_names = _BY_KEY[key]
    lines = [f"**{label}**", ""]
    modules = [_PLUGINS[n] for n in plugin_names if n in _PLUGINS]
    if not modules:
        lines.append("🚧 **Coming soon** — this module hasn't been added yet.")
    for module in modules:
        desc = getattr(module, "DESC", "")
        lines.append(f"**{module.TITLE}**" + (f" — _{desc}_" if desc else ""))
        for usage, description in getattr(module, "COMMANDS", []):
            lines.append(f"`{cfg.PREFIX}{usage}` — {description}")
        lines.append("")
    text = "\n".join(lines).strip()
    if len(text) > 3900:
        text = text[:3890] + "…"
    return text, [[Button.inline("⬅️ Back", f"hm:p:{page}".encode()), Button.inline("❌ Close ❌", b"hm:x")]]


# ── /start deployer card ────────────────────────────────────────────────────────────────
def _u16(s: str) -> int:
    return len(s.encode("utf-16-le")) // 2


def start_card():
    """Return (text, entities) for the /start screen.

    `entities` carries the bold title and the two collapsed quote blocks. It is None if this
    Telethon build can't express them, in which case the text alone still reads fine.
    """
    blocks = [("⚡ Key Capabilities & Engine", DEPLOYER_CAPABILITIES), ("🚀 4-Step Quick Setup Guide", DEPLOYER_STEPS)]
    try:
        from telethon.tl.types import MessageEntityBlockquote, MessageEntityBold
    except ImportError:
        MessageEntityBlockquote = MessageEntityBold = None

    text, entities = "", []

    def add(chunk: str, kind=None, **kw):
        nonlocal text
        if kind is not None and MessageEntityBold is not None:
            entities.append(kind(offset=_u16(text), length=_u16(chunk), **kw))
        text += chunk

    add(DEPLOYER_TITLE, MessageEntityBold if MessageEntityBold else None)
    add("\n\n")
    for title, body in blocks:
        quote = f"{title}\n{body}"
        if MessageEntityBlockquote is not None:
            add(quote, MessageEntityBlockquote, collapsed=True)
        else:
            add(quote)
        add("\n\n")
    add("Select an option below to get started.")
    return text, (entities or None)


def start_buttons(is_owner: bool):
    rows = [
        [Button.inline("📲 Login Userbot Your Account 📲", b"st:login")],
        [Button.inline("🛠 Help & Commands 🛠", b"hm:p:0")],
    ]
    last = []
    last.append(Button.url("👑 Owner", f"https://t.me/{cfg.OWNER_USERNAME}") if cfg.OWNER_USERNAME
                else Button.inline("👑 Owner", b"st:owner"))
    last.append(Button.url("📢 Update", cfg.UPDATE_URL) if cfg.UPDATE_URL
                else Button.inline("📢 Update", b"st:update"))
    rows.append(last)
    if is_owner:
        rows.append([Button.inline("🎛 Control Panel", b"st:panel")])
    return rows


def denied_card():
    """(text, entities) for the "not authorized" card shown to people an admin hasn't `.auth`-ed."""
    head = "✘ YOU ARE NOT AUTHORIZED TO USE THIS BOT"
    cmd = f"{cfg.PREFIX}auth @yourusername"
    tail = f", or contact @{cfg.OWNER_USERNAME}." if cfg.OWNER_USERNAME else "."
    text = f"{head}\nAsk an admin to run {cmd}{tail}"
    try:
        from telethon.tl.types import MessageEntityBlockquote, MessageEntityBold, MessageEntityCode
    except ImportError:
        return text, None
    entities = [
        MessageEntityBlockquote(offset=0, length=_u16(text)),
        MessageEntityBold(offset=0, length=_u16(head)),
        MessageEntityCode(offset=_u16(text[:text.index(cmd)]), length=_u16(cmd)),
    ]
    return text, entities


async def send_denied(event):
    text, entities = denied_card()
    if entities:
        await event.respond(text, formatting_entities=entities)
    else:
        await event.respond(text, parse_mode=None)
