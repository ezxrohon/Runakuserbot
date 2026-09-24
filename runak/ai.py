"""AI auto-reply for private chats (Groq). Off by default.

Safety defaults: private chats only, saved contacts only, one reply per 3 seconds and at most
30 per person per hour. Change the scope from the panel or with `.ai scope everyone`.
"""
import asyncio
import logging
import time
from collections import defaultdict, deque

import httpx

from .. import config as cfg
from ..context import say

log = logging.getLogger("runak.ai")

NAME = "ai"
TITLE = "🤖 AI Auto-Reply"
DESC = "Friendly AI replies in private chats (needs GROQ_API_KEY)."
DEFAULT_ON = False
TOGGLE = True
COMMANDS = [
    ("ai on|off|status", "Switch AI replies"),
    ("ai scope contacts|everyone", "Who gets AI replies"),
    ("ask <question>", "Ask the AI something privately"),
    ("setprompt <text>", "Change the AI personality"),
    ("resetprompt", "Restore the default personality"),
]

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
HOURLY_CAP = 30


def setup(ctx):
    history = defaultdict(lambda: deque(maxlen=10))
    locks = defaultdict(asyncio.Lock)
    last_reply = {}
    hourly = defaultdict(deque)
    http = httpx.AsyncClient(timeout=45.0)

    def prompt() -> str:
        return ctx.store.data["ai"].get("prompt") or cfg.DEFAULT_PROMPT

    def scope() -> str:
        return ctx.store.data["ai"].get("scope", "contacts")

    async def ask(uid, text: str, remember: bool = True) -> str:
        past = list(history[uid]) if remember else []
        messages = [{"role": "system", "content": prompt()}, *past, {"role": "user", "content": text}]
        resp = await http.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {cfg.GROQ_API_KEY}"},
            json={"model": cfg.GROQ_MODEL, "messages": messages, "temperature": 0.7, "max_tokens": 400},
        )
        resp.raise_for_status()
        answer = resp.json()["choices"][0]["message"]["content"].strip()
        if not answer:
            raise RuntimeError("empty answer")
        if remember:
            history[uid].append({"role": "user", "content": text})
            history[uid].append({"role": "assistant", "content": answer})
        return answer

    @ctx.command(NAME, "ai", always=True)
    async def ai_cmd(event, arg):
        parts = arg.lower().split()
        choice = parts[0] if parts else ""
        if choice == "on":
            if not cfg.GROQ_API_KEY:
                await say(event, "⚠️ Set `GROQ_API_KEY` in your environment first.")
                return
            ctx.set_enabled(NAME, True)
            await say(event, f"🤖 AI replies **ON** (private chats, scope: **{scope()}**).")
        elif choice == "off":
            ctx.set_enabled(NAME, False)
            await say(event, "🤖 AI replies **OFF**.")
        elif choice == "scope" and len(parts) > 1 and parts[1] in ("contacts", "everyone"):
            ctx.store.data["ai"]["scope"] = parts[1]
            ctx.store.save_soon()
            await say(event, f"🤖 AI scope: **{parts[1]}**.")
        else:
            state = "ON" if ctx.enabled(NAME) else "OFF"
            await say(event, f"🤖 AI replies: **{state}**\nScope: **{scope()}**\nModel: `{cfg.GROQ_MODEL}`")

    @ctx.command(NAME, "ask", always=True)
    async def ask_cmd(event, arg):
        if not cfg.GROQ_API_KEY:
            await say(event, "⚠️ Set `GROQ_API_KEY` in your environment first.")
            return
        if not arg:
            await say(event, "Usage: `.ask <question>`")
            return
        await say(event, "🤔 Thinking…")
        try:
            answer = await ask(None, arg, remember=False)
        except Exception as exc:
            log.warning("AI ask failed: %s", type(exc).__name__)
            await say(event, "❌ The AI service didn't answer. Try again later.")
            return
        await say(event, answer[:4000], md=False)

    @ctx.command(NAME, "setprompt", always=True)
    async def set_prompt(event, arg):
        if not arg:
            await say(event, "Usage: `.setprompt <personality>`")
            return
        ctx.store.data["ai"]["prompt"] = arg[:1500]
        ctx.store.save_soon()
        await say(event, "✅ AI personality updated.")

    @ctx.command(NAME, "resetprompt", always=True)
    async def reset_prompt(event, arg):
        ctx.store.data["ai"]["prompt"] = None
        ctx.store.save_soon()
        await say(event, "✅ AI personality reset to default.")

    @ctx.on_dm(NAME)
    async def reply(event):
        text = (event.raw_text or "").strip()
        if not text or not cfg.GROQ_API_KEY or ctx.store.data["afk"]["on"]:
            return
        sender = await ctx.human_sender(event)
        if not sender:
            return
        if scope() == "contacts" and not getattr(sender, "contact", False):
            return
        uid = sender.id
        now = time.monotonic()
        if now - last_reply.get(uid, 0) < 3:  # simple anti-flood
            return
        recent = hourly[uid]
        while recent and now - recent[0] > 3600:
            recent.popleft()
        if len(recent) >= HOURLY_CAP:
            return
        last_reply[uid] = now
        recent.append(now)
        async with locks[uid]:
            try:
                async with ctx.client.action(event.chat_id, "typing"):
                    answer = await ask(uid, text[:2000])
            except Exception as exc:
                log.warning("AI reply failed: %s", type(exc).__name__)
                return
            for i in range(0, len(answer), 4000):
                await event.respond(answer[i : i + 4000])
