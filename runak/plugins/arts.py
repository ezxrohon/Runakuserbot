"""Native text-art collection migrated from the legacy plugin."""
from ..context import say

NAME = "arts"
TITLE = "🎨 Arts"
DESC = "Offline ASCII and emoji art commands."
DEFAULT_ON = True
ARTS = {
    "sshit": "Ah shit, here we go again. 😅", "elove": "💖 Love 💖", "monster": "▄███████▄\n█▼▼▼▼▼█\n█████████",
    "pig": "┈┏━╮╭━┓\n┈┃┏┗┛┓┃ 🐷", "gun": "▐██████▌ 🔫", "dog": "🐶 Woof!", "hey": "╔━━╗\n║ Hey! ║\n╚━━╝",
    "couple": "💑 Love you forever", "india": "🇮🇳 INDIA 🇮🇳", "wc": "╔══════════╗\n║ Welcome! ║\n╚══════════╝",
    "snk": "🐍➰🐍➰🐍", "bye": "👋 Bye friends!", "shitos": "╭━━━╮\n┃ HI ┃\n╰━━━╯", "dislike": "👎 Dislike",
}
COMMANDS = [(name, "Show art") for name in ARTS] + [(name, "Show art with a name") for name in ("carry", "ded", "sthink", "sfrog", "sdead", "strump", "schina")]


def setup(ctx):
    for command, art in ARTS.items():
        @ctx.command(NAME, command)
        async def show(event, arg, art=art):
            await say(event, art, md=False)
    for command in ("carry", "ded", "sthink", "sfrog", "sdead", "strump", "schina"):
        @ctx.command(NAME, command)
        async def named(event, arg, command=command):
            await say(event, f"{command.title()} ~> {arg or 'friend'}", md=False)
