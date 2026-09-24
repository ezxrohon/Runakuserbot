"""Reminders. They are delivered to YOUR Saved Messages only — never to anyone else."""
import asyncio
import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .. import config as cfg
from ..context import say
from ..helpers import fmt_duration, parse_duration

log = logging.getLogger("runak.remind")

NAME = "remind"
TITLE = "⏰ Reminders"
DESC = "Reminders sent to your Saved Messages."
DEFAULT_ON = True
COMMANDS = [
    ("remind <10m|2h|1d|1h30m> <text>", "Set a reminder"),
    ("reminders", "List pending reminders"),
    ("unremind <n|all>", "Delete a reminder"),
]

MAX_REMINDERS = 15
MAX_SECONDS = 30 * 86400


def local_time(ts: float) -> str:
    try:
        zone = ZoneInfo(cfg.TIMEZONE)
    except (ZoneInfoNotFoundError, ValueError):
        zone = ZoneInfo("UTC")
    return f"{datetime.fromtimestamp(ts, zone):%d %b %H:%M %Z}"


def setup(ctx):
    def items() -> list:
        return ctx.store.data["reminders"]

    async def deliver_forever():
        while True:
            await asyncio.sleep(15)
            if not ctx.enabled(NAME):
                continue
            now = time.time()
            for item in [r for r in items() if r["due"] <= now]:
                try:
                    await ctx.client.send_message("me", f"⏰ Reminder: {item['text']}", parse_mode=None)
                except Exception as exc:
                    log.warning("Reminder delivery failed (%s) - will retry", type(exc).__name__)
                    continue
                if item in items():
                    items().remove(item)
                    ctx.store.save_soon()

    ctx.tasks.append(asyncio.get_running_loop().create_task(deliver_forever()))

    @ctx.command(NAME, "remind")
    async def remind(event, arg):
        when, _, text = arg.partition(" ")
        seconds = parse_duration(when) if when else None
        text = text.strip()
        if not seconds or not text:
            await say(event, "Usage: `.remind 30m call mom` (units: s, m, h, d — e.g. `1h30m`)")
            return
        if seconds > MAX_SECONDS:
            await say(event, "❌ Maximum is 30 days.")
            return
        if len(items()) >= MAX_REMINDERS:
            await say(event, "❌ Too many reminders. Delete one first.")
            return
        items().append({"due": time.time() + seconds, "text": text[:300]})
        items().sort(key=lambda r: r["due"])
        if not ctx.store.fits():
            items().pop()
            await say(event, "❌ Storage is full. Delete a note or reminder first.")
            return
        ctx.store.save_soon()
        await say(event, f"⏰ Reminder set for **{local_time(time.time() + seconds)}** (in {fmt_duration(seconds)}).")

    @ctx.command(NAME, "reminders")
    async def show(event, arg):
        if not items():
            await say(event, "⏰ No pending reminders.")
            return
        lines = [f"`{i}.` {local_time(r['due'])} — {r['text']}" for i, r in enumerate(items(), 1)]
        await say(event, "⏰ **Reminders**\n" + "\n".join(lines))

    @ctx.command(NAME, "unremind")
    async def unremind(event, arg):
        if arg.lower() == "all":
            items().clear()
        elif arg.isdigit() and 1 <= int(arg) <= len(items()):
            items().pop(int(arg) - 1)
        else:
            await say(event, "Usage: `.unremind <number>` or `.unremind all`")
            return
        ctx.store.save_soon()
        await say(event, "🗑 Done.")
