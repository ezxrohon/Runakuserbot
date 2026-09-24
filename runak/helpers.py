"""Pure helper functions (no Telegram imports, so they are easy to test)."""
import ast
import operator
import re

_BIN = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        if isinstance(node.value, bool):
            raise ValueError("booleans are not allowed")
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and (abs(right) > 10 or abs(left) > 10**6):
            raise ValueError("exponent too large")
        return _BIN[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_eval(node.operand))
    raise ValueError("only basic arithmetic is supported")


def calculate(expression: str):
    """Safely evaluate basic arithmetic. Never uses eval()."""
    if len(expression) > 120:
        raise ValueError("expression too long")
    return _eval(ast.parse(expression, mode="eval"))


_SMALL = str.maketrans(
    "abcdefghijklmnopqrstuvwxyz",
    "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ",
)


def small_caps(text: str) -> str:
    return text.lower().translate(_SMALL)


def fmt_duration(seconds: float) -> str:
    seconds = int(max(0, seconds))
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    if minutes or hours or days:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def parse_duration(text: str):
    """'90s', '10m', '2h', '1d', '1h30m' -> seconds, or None if it isn't a duration."""
    text = text.strip().lower()
    parts = re.findall(r"(\d+)([smhd])", text)
    if not parts or "".join(n + u for n, u in parts) != text:
        return None
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return sum(int(n) * units[u] for n, u in parts)


def _offset_font(upper_start: int, lower_start: int):
    def convert(text: str) -> str:
        out = []
        for ch in text:
            if "A" <= ch <= "Z":
                out.append(chr(upper_start + ord(ch) - 65))
            elif "a" <= ch <= "z":
                out.append(chr(lower_start + ord(ch) - 97))
            else:
                out.append(ch)
        return "".join(out)

    return convert


FONTS = {
    "small": small_caps,
    "bold": _offset_font(0x1D400, 0x1D41A),
    "sans": _offset_font(0x1D5D4, 0x1D5EE),
    "mono": _offset_font(0x1D670, 0x1D68A),
    "circle": _offset_font(0x24B6, 0x24D0),
}
