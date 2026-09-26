"""Small, dependency-free text art commands."""
from ..context import say

NAME = "funarts"
TITLE = "🎭 Fun Arts"
DESC = "Show harmless offline emoji and text art."
DEFAULT_ON = True
ARTS = {
    "join": "┏━━━━━━━━━━━━┓\n┃ Welcome! 👋 ┃\n┗━━━━━━━━━━━━┛",
    "climb": "😏/\n/▌\n/ \\\n🧗 Climbing!",
    "aag": "😲💨 🔥🔥🔥",
    "push": "😎🤲 ━━━━━━━ 💪",
    "work": "📚💻☕ Keep going!",
    "lmoon": "🌕🌖🌗🌘🌑🌒🌓🌔",
    "city": "☁️ ☁️ 🌞 ☁️\n🏢🏨🏫🏥\n🌳 🚗 🚌 🌴",
}
COMMANDS = [(name, "Show fun art") for name in ARTS]


def setup(ctx):
    for command, art in ARTS.items():
        @ctx.command(NAME, command)
        async def show(event, arg, art=art):
            await say(event, art, md=False)
