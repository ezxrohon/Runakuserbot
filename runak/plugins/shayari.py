"""Offline Hindi/Urdu shayari plugin using the shared Runak context."""
import random

from ..context import say

NAME = "shayari"
TITLE = "✍️ Shayari"
DESC = "Offline love, sad, friendship and motivational poetry."
DEFAULT_ON = True
COMMANDS = [("shayari [category]", "Show a random poem")]

POEMS = {
    "love": [
        "Aapki muskurahat ne hamara hosh uda diya,\nAapki ek hasi ne din bana diya. ❤️",
        "Tum paas ho ya door, dil mein tumhari jagah hamesha hai. 💞",
    ],
    "sad": ["Khamoshi se bikharna aa gaya hai,\nHumein ab khud mein rehna aa gaya hai. 💔"],
    "dosti": ["Dost woh hai jo rote hue ko hasa de. 🤝"],
    "motivational": ["Hauslon se udaan hoti hai, pankhon se nahi. ✨"],
}


def setup(ctx):
    @ctx.command(NAME, "shayari")
    async def shayari(event, arg):
        category = arg.strip().lower() or "love"
        if category not in POEMS:
            await say(event, "❌ Categories: " + ", ".join(sorted(POEMS)))
            return
        await say(event, f"✍️ **{category.title()} Shayari**\n\n{random.choice(POEMS[category])}")
