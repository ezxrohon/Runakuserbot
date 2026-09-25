"""Native plugin registry.

Legacy Pyrogram/CipherElite modules are registered only after being adapted to
Runak's shared Telethon context.
"""
from . import (
    core, afk, ai, tools, notes, remind, purge, sticker, shayari, clone,
    animation1, animation4, animation5, flashvault, fonts, love, namestyle,
    raid, spam, trolls, animation, autoreact, broadcast, tagall, all_tag,
)

ALL = [
    core, afk, ai, tools, notes, remind, purge, sticker, shayari, clone,
    animation1, animation4, animation5, flashvault, fonts, love, namestyle,
    raid, spam, trolls, animation, autoreact, broadcast, tagall, all_tag,
]
