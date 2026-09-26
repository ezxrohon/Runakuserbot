"""Developer utilities for checking plugin files safely."""
import ast
from pathlib import Path
from ..context import say

NAME = "install"
TITLE = "🧩 Plugin Checker"
DESC = "Validate local Python plugin files without installing arbitrary packages."
DEFAULT_ON = False
COMMANDS = [("plugincheck [file]", "Validate a plugin's Python syntax")]


def setup(ctx):
    @ctx.command(NAME, "plugincheck")
    async def plugincheck(event, arg):
        name = (arg or "").strip() or ""
        if not name:
            await say(event, "Usage: `.plugincheck <path>`", md=False)
            return
        path = Path(name)
        if not path.is_file() or path.suffix != ".py":
            await say(event, "❌ Provide an existing `.py` file.", md=False)
            return
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            await say(event, f"❌ Plugin is invalid: {exc}", md=False)
            return
        await say(event, f"✅ `{path}` has valid Python syntax.", md=False)
