import time

from ..context import say
from ..helpers import fmt_duration

NAME = "afk"
TITLE = "🌙 AFK"
DESC = "Auto-notify people who DM you while you're away (once per person)."
DEFAULT_ON = True
COMMANDS = [
    ("afk [reason]", "Turn AFK on"),
    ("unafk", "Turn AFK off"),
]


def setup(ctx):
    @ctx.command(NAME, "afk")
    async def afk_on(event, arg):
        ctx.store.data["afk"].update(
            on=True,
            reason=arg[:300] or "I'm away right now. I'll reply when I'm back.",
            since=int(time.time()),
        )
        ctx.afk_notified.clear()
        ctx.store.save_soon()
        await say(event, f"🌙 **AFK on.**\nReason: {ctx.store.data['afk']['reason']}")

    @ctx.command(NAME, "unafk")
    async def afk_off(event, arg):
        ctx.store.data["afk"]["on"] = False
        ctx.afk_notified.clear()
        ctx.store.save_soon()
        await say(event, "✅ **AFK off.** Welcome back!")

    @ctx.on_dm(NAME)
    async def notify(event):
        afk = ctx.store.data["afk"]
        if not afk["on"]:
            return
        sender = await ctx.human_sender(event)
        if not sender or sender.id in ctx.afk_notified:
            return
        ctx.afk_notified.add(sender.id)
        away = fmt_duration(time.time() - afk["since"])
        await event.respond(f"🌙 **AFK** — {afk['reason']}\n⏱ Away for {away}")
