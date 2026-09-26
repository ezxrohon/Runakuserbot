"""Offline meme and reaction text commands."""
import random
from ..context import say

NAME = "memestext"
TITLE = "😂 Meme Text"
DESC = "Random harmless reactions and meme text."
DEFAULT_ON = True
TEXT = {
    "congo": ["🎉 Congratulations!", "👏 Well done!"],
    "shg": ["┐(´д｀)┌", "¯\\_(ツ)_/¯"],
    "runs": ["🏃 Runs away dramatically.", "🏃💨 Gone!"],
    "noob": ["Try again, champ 😄", "Practice makes progress."],
    "insult": ["Your humor needs an update 😄", "The roast failed safely."],
    "pro": ["🔥 Pro mode activated!", "🏆 Absolute legend."],
    "10iq": ["🧠 10 IQ moment."],
    "fp": ["🤦 Facepalm."],
    "bt": ["/BLUETEXT /MUST /CLICK"],
    "session": ["ℹ️ Session tips: keep one active Telegram client per session."],
}
COMMANDS = [(name, "Show a random reaction") for name in TEXT] + [("react [type]", "Show a face reaction")]
REACTIONS = ["( ͡° ͜ʖ ͡°)", "(｡•̀ᴗ-)✧", "¯\\_(ツ)_/¯", "ಠ_ಠ", "❤️"]


def setup(ctx):
    for command, choices in TEXT.items():
        @ctx.command(NAME, command)
        async def meme(event, arg, choices=choices):
            await say(event, random.choice(choices), md=False)

    @ctx.command(NAME, "react")
    async def react(event, arg):
        await say(event, random.choice(REACTIONS), md=False)
