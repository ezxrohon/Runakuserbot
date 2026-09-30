"""Compatibility wrapper for the native raid-burst protection."""
from .controller_features import setup as _setup
NAME = "raid"
TITLE = "🛡 Raid Protection"
DESC = "Detects message bursts and can remove/restrict accounts in a raid-like burst."
DEFAULT_ON = True
COMMANDS = []

def setup(ctx):
    # The full implementation lives in controller_features so state and handlers are shared.
    return None
