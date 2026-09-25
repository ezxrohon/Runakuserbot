"""Interactive, paginated plugin category menu for the userbot client."""
from telethon import Button, events

NAME = "plugin_menu"
TITLE = "🧩 Plugin Categories"
DESC = "Browse enabled plugins by category with inline pages."
DEFAULT_ON = True
COMMANDS = [("plugins", "Open the categorized plugin menu")]

_CATEGORY_NAMES = {
    "core": "⚙️ Core",
    "ai": "🤖 AI",
    "tools": "🛠 Tools",
    "media": "🎨 Media",
    "animations": "🎞 Animations",
    "social": "💬 Social",
    "admin": "🛡 Admin",
    "utilities": "🔧 Utilities",
    "other": "📦 Other",
}
_PAGE_SIZE = 6


def _category(module):
    value = getattr(module, "CATEGORY", None)
    if value:
        return str(value).lower()
    name = getattr(module, "NAME", "")
    if name == "core":
        return "core"
    if name in {"ai"}:
        return "ai"
    if name in {"tools", "notes", "remind", "purge", "autoreact", "plugin_menu"}:
        return "utilities"
    if name.startswith("animation") or name == "animation":
        return "animations"
    if name in {"sticker", "fonts", "love", "namestyle", "flashvault"}:
        return "media"
    if name in {"clone", "raid", "spam", "trolls", "tagall", "all_tag", "broadcast"}:
        return "social"
    return "other"


def _label(category):
    return _CATEGORY_NAMES.get(category, f"📦 {category.replace('_', ' ').title()}")


def _group(ctx):
    result = {}
    for module in ctx.registry:
        if not ctx.is_enabled(module):
            continue
        result.setdefault(_category(module), []).append(module)
    return {key: sorted(value, key=lambda item: item.TITLE) for key, value in sorted(result.items())}


def _category_view(ctx, page=0):
    groups = _group(ctx)
    names = list(groups)
    pages = max(1, (len(names) + _PAGE_SIZE - 1) // _PAGE_SIZE)
    page = max(0, min(page, pages - 1))
    start = page * _PAGE_SIZE
    rows = [[Button.inline(_label(name), f"pluginmenu:category:{name}".encode()) for name in names[start:start + 2]]]
    rows = [row for row in rows if row]
    nav = []
    if page:
        nav.append(Button.inline("⬅️", f"pluginmenu:categories:{page - 1}".encode()))
    nav.append(Button.inline(f"{page + 1}/{pages}", b"pluginmenu:noop"))
    if page + 1 < pages:
        nav.append(Button.inline("➡️", f"pluginmenu:categories:{page + 1}".encode()))
    rows.append(nav)
    return "**🧩 Plugin Categories**\nChoose a category:", rows


def _plugin_view(ctx, category):
    groups = _group(ctx)
    modules = groups.get(category, [])
    rows = []
    for module in modules:
        rows.append([Button.inline(module.TITLE, f"pluginmenu:plugin:{module.NAME}:{category}".encode())])
    rows.append([Button.inline("⬅️ Categories", b"pluginmenu:categories:0")])
    return f"**{_label(category)}**\nChoose a plugin:", rows


def _detail_view(ctx, name, category):
    module = next((item for item in ctx.registry if item.NAME == name), None)
    if module is None:
        return "Plugin not found.", [[Button.inline("⬅️ Categories", b"pluginmenu:categories:0")]]
    lines = [f"**{module.TITLE}**", getattr(module, "DESC", ""), ""]
    for usage, description in getattr(module, "COMMANDS", []):
        lines.append(f"`{usage}` — {description}")
    return "\n".join(lines), [[Button.inline(f"⬅️ {_label(category)}", f"pluginmenu:category:{category}".encode())]]


def setup(ctx):
    @ctx.command(NAME, "plugins")
    async def plugins(event, arg):
        text, buttons = _category_view(ctx)
        await event.respond(text, buttons=buttons)

    @ctx.client.on(events.CallbackQuery(data=b"pluginmenu:noop"))
    async def noop(event):
        await event.answer()

    @ctx.client.on(events.CallbackQuery(pattern=b"pluginmenu:"))
    async def callbacks(event):
        parts = event.data.decode().split(":")
        if len(parts) < 3:
            return
        if parts[1] == "categories":
            text, buttons = _category_view(ctx, int(parts[2]))
        elif parts[1] == "category":
            text, buttons = _plugin_view(ctx, parts[2])
        elif parts[1] == "plugin" and len(parts) >= 4:
            text, buttons = _detail_view(ctx, parts[2], parts[3])
        else:
            return
        await event.answer()
        await event.edit(text, buttons=buttons)
