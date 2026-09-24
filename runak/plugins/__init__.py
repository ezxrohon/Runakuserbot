"""Curated plugin list. Plugins are loaded from this fixed list only —
there is no remote installer and no auto-updater, by design."""
from . import core, afk, ai, tools, notes, remind, purge, sticker, shayari

ALL = [core, afk, ai, tools, notes, remind, purge, sticker, shayari]
