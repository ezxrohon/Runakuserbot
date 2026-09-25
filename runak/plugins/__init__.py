"""Curated native plugins.

Every module in this list uses the shared Runak context.  Legacy plugins that
created their own Telethon clients or imported a different userbot framework
are intentionally not loaded.
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
    animation1, flashvault, fonts, love, namestyle, raid, spam, trolls,
]
