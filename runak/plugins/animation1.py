"""Small offline animation/status commands."""
from ..context import say

NAME = "animation1"
TITLE = "🎬 Animations"
DESC = "Small harmless text animations and reactions."
DEFAULT_ON = True
COMMANDS = [("stupid|bombs|call|kill|wtf|ding|hypno|candy|gangasta|charging", "Show a reaction")]


def setup(ctx):
    messages = {
        "stupid": "🧠➡️🗑️ Just a harmless animation.", "bombs": "💣💣💣 → 💥",
        "call": "📞 Connecting… Call ended.", "kill": "🎯 Game animation only — nobody was harmed.",
        "wtf": "What the… 🤨", "ding": "🔔 Ding dong!", "hypno": "🌀 Hypno…",
        "candy": "🍦🍧🍩🍪🎂🍰🧁🍫🍬🍭", "gangasta": "🔥 Everybody is gangsta until I arrive.",
        "charging": "🔋 Charging complete: 100%",
    }
    for command, text in messages.items():
        @ctx.command(NAME, command)
        async def reaction(event, arg, text=text):
            await say(event, text, md=False)
