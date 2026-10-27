import random
from runak.helpers import safe_edit
from runak.plugins.vortex_core import register_cmd

SHAYARI_DB = [
    "🌙✨ Raat khamosh hai, magar yaadein bolti hain;\n💖 Dil door sahi, par dhadkanein saath chalti hain.",
    "🌹 Har phool ki khushboo khaas nahi hoti;\n💫 Har mulaqat ek ittefaq nahi hoti.",
    "🔥 Stay kind, stay focused, keep growing with Vortex-Runak!"
]

@register_cmd("shayari")
async def cmd_shayari(event, _):
    await safe_edit(event, random.choice(SHAYARI_DB))

@register_cmd("joke")
async def cmd_joke(event, _):
    await safe_edit(event, "😂 Teacher: Late kyun aaye? Student: Sir, sapne mein school aa gaya tha!")
