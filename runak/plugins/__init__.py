"""Native plugin registry.

Only modules implementing the shared Runak context are loaded.  Legacy
Pyrogram/CipherElite modules are intentionally not imported because they cannot
work in this Telethon application.
"""
from . import (
    core,
    afk,
    ai,
    tools,
    notes,
    remind,
    purge,
    sticker,
    shayari,
    clone,
    animation1,
    animation4,
    animation5,
    flashvault,
    fonts,
    love,
    namestyle,
    raid,
    spam,
    trolls,
)

ALL = [
    core, afk, ai, tools, notes, remind, purge, sticker, shayari, clone,
    animation1, animation4, animation5, flashvault, fonts, love, namestyle,
    raid, spam, trolls,
]
