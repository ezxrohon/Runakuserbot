# 🫧🦋 ʀuɴAk userbot

A small, safety-first Telegram userbot (Telethon) that you control from a **bot panel**, built to run on a
**Render free web service**.

- Your account runs the commands (`.ping`, `.calc`, …). **Only your own outgoing messages can trigger them.**
- A private **bot panel** (from @BotFather) lets you switch plugins, AFK and the AI on/off with buttons.
- No hidden admins, no built-in API keys, no remote plugin installer, no auto-updater.

## Plugins (all local or owner-only)

| Plugin | Commands |
|---|---|
| ⚙️ Core (always on) | `.ping` `.alive` `.id` `.info` `.help` |
| 🌙 AFK | `.afk [reason]` `.unafk` — one away-message per person |
| 🤖 AI Auto-Reply (off by default) | `.ai on/off/status` `.ai scope contacts/everyone` `.ask` `.setprompt` `.resetprompt` |
| 🧰 Tools & Fun | `.calc` `.upper` `.lower` `.reverse` `.small` `.font` `.b64` `.unb64` `.pass` `.time` `.dice` `.flip` `.8ball` |
| 📝 Notes | `.save` `.get` `.notes` `.clear` |
| ⏰ Reminders | `.remind 30m text` `.reminders` `.unremind` — delivered to *your* Saved Messages |
| 🧹 Clean-up | `.del` `.purge` — only ever deletes **your own** messages |

Deliberately **not** included: spam/raid/mass-add/broadcast tools, account cloning, `eval`/shell commands,
remote plugin installers, auto-updaters, and any "session maker" bot. They get accounts banned or leak them.

## Deploy on Render (free)

1. **Telegram API keys** — log in at <https://my.telegram.org> → *API development tools* → note `API_ID` and `API_HASH`.
2. **Panel bot** — talk to [@BotFather](https://t.me/BotFather) → `/newbot` → copy the `BOT_TOKEN`.
3. **Session string** — on **your own computer** (never on a server, never via someone else's bot):
   ```bash
   pip install telethon
   python create_session.py
   ```
   Log in with your phone number; copy the printed string → this is `TELEGRAM_SESSION`. Treat it like a password.
4. **GitHub** — push this folder to a *private* repository (`.env` is git-ignored).
5. **Render** — *New → Blueprint* → pick the repo (it reads `render.yaml`, plan *Free*), then fill in
   `API_ID`, `API_HASH`, `TELEGRAM_SESSION`, `BOT_TOKEN` (and optionally `GROQ_API_KEY`, `TIMEZONE`) → *Apply*.
6. When the log shows `is online as …`, open your bot in Telegram and send `/start`. Only you get the panel.

### Free-tier facts you should know
- **Sleeping:** Render spins a free web service down after 15 minutes without inbound traffic. A sleeping
  userbot is an offline userbot. `KEEPALIVE=1` (default) makes the bot ping its own public URL every 10 minutes;
  you can also use an external pinger on `/healthz`. Render staff have said deliberately keeping free services awake
  goes against the spirit of the free tier, so this could stop working — a paid instance is the reliable option.
- **750 free hours/month** per workspace ≈ one always-on service. Don't run other free services alongside it.
- **Settings survive restarts** because they're saved as one message (starting with `runak-store:v1`) in your own
  *Saved Messages*. Please don't delete it. It holds a small amount of data (a few notes, AFK text, reminders).
- **One session, one place.** Never run the same `TELEGRAM_SESSION` locally and on Render at the same time —
  Telegram will invalidate it.
- Restarting from the panel briefly logs the panel bot in again; avoid restart loops.

## Environment variables

| Name | Required | Notes |
|---|---|---|
| `API_ID`, `API_HASH` | ✅ | from my.telegram.org |
| `TELEGRAM_SESSION` | ✅ | from `create_session.py` |
| `BOT_TOKEN` | recommended | panel bot; without it the userbot runs with no panel |
| `GROQ_API_KEY` | optional | enables the AI plugin |
| `PREFIX` | optional | command prefix, default `.` |
| `TIMEZONE` | optional | e.g. `Asia/Kolkata`, default `UTC` |
| `KEEPALIVE` | optional | `0` disables the self-ping |

## Rebranding

Everything user-visible comes from `runak/branding.py` (`BRAND`, `TAGLINE`). Change it there.

## Develop / test

```bash
pip install -r requirements.txt
python tests/test_helpers.py
python tests/test_smoke.py     # offline: runs every plugin and the panel against fake Telegram objects
python main.py                 # needs the env vars above
```

## Adding your own plugin

Copy any file in `runak/plugins/`, define `NAME`, `TITLE`, `DESC`, `DEFAULT_ON`, `COMMANDS` and `setup(ctx)`,
then list it in `runak/plugins/__init__.py`. Plugins are loaded only from that fixed list.

## License

MIT — see `LICENSE`.
