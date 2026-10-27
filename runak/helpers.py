"""Pure helper functions and Telegram configuration/client setup."""
import os
import json
import ast
import operator
import re
from telethon import TelegramClient
from telethon.sessions import StringSession
from runak.config import API_ID, API_HASH, SESSIONS, OWNER_ID

SESSION = SESSIONS[0] if SESSIONS else ""

BASE_DIR = os.getcwd()
DOWNLOAD_PATH = os.path.join(BASE_DIR, "downloads")
TEMP_PATH = os.path.join(BASE_DIR, "temp")
os.makedirs(DOWNLOAD_PATH, exist_ok=True)
os.makedirs(TEMP_PATH, exist_ok=True)

bot = TelegramClient(StringSession(SESSION), API_ID, API_HASH, retry_delay=3)

ADMINS_FILE = "admins.json"
NOTES_FILE = "notes.json"
BANNER_FILE = "banner_msg_id.txt"

admins = set()
notes = {}
menu_banner_msg = None
auto_react_emoji = None

muted_users = set()
global_muted = set()
reply_users = set()
rr_users = set()
flag_users = set()
hrr_users = set()
replygod_users = set()
replyyorichi_users = {}
spray_tasks = {}
group_locks = set()
START_TIME = 0

def load_admins():
    global admins
    try:
        if os.path.isfile(ADMINS_FILE):
            with open(ADMINS_FILE, "r", encoding="utf-8") as f:
                admins = set(int(x) for x in json.load(f))
    except Exception:
        admins = set()

def save_admins():
    try:
        with open(ADMINS_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(list(admins)), f, indent=2)
    except Exception:
        pass

def is_admin(uid: int) -> bool:
    return uid == OWNER_ID or uid in admins

async def safe_edit(event, text: str):
    if not text:
        return
    try:
        return await event.edit(text)
    except Exception:
        try:
            msg = await event.reply(text)
            if event.out:
                await event.delete()
            return msg
        except Exception:
            pass

async def get_targets(event, arg: str = "") -> set:
    targets = set()
    if event.is_reply:
        try:
            reply = await event.get_reply_message()
            if reply and reply.sender_id:
                targets.add(int(reply.sender_id))
        except Exception:
            pass
    if arg:
        for part in arg.strip().split():
            if part.isdigit():
                targets.add(int(part))
            else:
                try:
                    ent = await bot.get_entity(part)
                    if ent and ent.id:
                        targets.add(int(ent.id))
                except Exception:
                    pass
    try:
        me = await bot.get_me()
        targets.discard(me.id)
    except Exception:
        pass
    return targets


# ────────────────────────────────────────────────
#                 RUNAK UTILITIES
# ────────────────────────────────────────────────

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
