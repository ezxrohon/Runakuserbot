# 🫧🦋 ʀuɴAk userbot

A feature-rich Telegram userbot (Telethon) with a **premium colourful control panel**, built for a
**Render web service**. Supports **multiple accounts of your own** in one deployment, with per-account settings
stored in **Firebase (Firestore)** or Saved Messages.

- Each of your accounts runs its own commands (`.ping`, `.calc`, …). **Only that account's own outgoing
  messages can trigger them** — one account can never trigger another's commands.
- One private **bot panel** (from @BotFather) controls all of your accounts, with an account switcher when
  you run more than one.
- No hidden admins, no built-in API keys, no remote plugin installer, no auto-updater.

## Plugins (all local or owner-only)

| Plugin | Commands |
|---|---|
| ⚙️ Core (always on) | `.ping` `.alive` `.id` `.info` `.help` |
| 🌙 AFK | `.afk [reason]` `.unafk` — one away-message per person |
| 🤖 AI Auto-Reply (off by default) | `.ai on/off/status` `.ai scope contacts/everyone` `.ai smallcaps on/off` `.ask` `.setprompt` `.resetprompt` — replies are sent in ꜱᴍᴀʟʟ ᴄᴀᴘꜱ by default |
| 🧰 Tools & Fun | `.calc` `.upper` `.lower` `.reverse` `.small` `.font` `.b64` `.unb64` `.pass` `.time` `.dice` `.flip` `.8ball` |
| 📝 Notes | `.save` `.get` `.notes` `.clear` |
| ⏰ Reminders | `.remind 30m text` `.reminders` `.unremind` — delivered to *your* Saved Messages |
| 🧹 Clean-up | `.del` `.purge` — only ever deletes **your own** messages |
| 🎟 Sticker Reply | `.stickeron` / `.stickeroff` (reply to someone) — when that person later sends **a sticker**, they get a random sticker back from your Saved Messages, instead of any other reply |

The shipped registry keeps the project local and extensible. Existing feature plugins can be enabled from the panel;
network-facing plugin installation and arbitrary shell/eval execution are not part of the core.

## Bot screens

- Access: the bot is closed by default. Run `.auth @username` from your account to let someone in; everyone else sees
  “YOU ARE NOT AUTHORIZED TO USE THIS BOT”. `.unauth` removes them, `.authlist` shows who's in.
- `/start` (authorized users) — deployer card with Login, Help & Commands, Owner and Update buttons.
- `/help` (anyone) — paged category menu (Prev / Next / Close); each category lists its real commands.
- `/login` (anyone, when `VAULT_KEY` + Firebase are set) — consent screen, phone, code, optional 2FA. One login creates a
  Telethon session (runs the userbot) and a second independent session packed as a Pyrogram string (for voice-chat
  features). Both are stored encrypted. `/logout` revokes and deletes them.
- `/panel` (owner only) — the control panel. Login is owner-only: it connects a StringSession you provide.

## Deploy on Render (free)

1. **Telegram API keys** — log in at <https://my.telegram.org> → *API development tools* → note `API_ID` and
   `API_HASH`. The same `API_ID`/`API_HASH` pair is reused for every account you run — that's normal.
2. **Panel bot** — talk to [@BotFather](https://t.me/BotFather) → `/newbot` → copy the `BOT_TOKEN`. One panel
   bot controls all of your accounts.
3. **Session string(s)** — on **your own computer** (never on a server, never via someone else's bot), once
   per account you want to run:
   ```bash
   pip install telethon
   python create_session.py
   ```
   Log in with that account's phone number; copy the printed string. Treat every session string like a
   password — whoever has it controls that account.
   - **One account:** set it as `TELEGRAM_SESSION`.
   - **Several accounts (all your own):** set `TELEGRAM_SESSIONS` to the session strings separated by commas,
     e.g. `TELEGRAM_SESSIONS=session_one,session_two,session_three`.
4. **Firebase (Firestore) for storage** — optional but recommended, especially with multiple accounts:
   - Go to the [Firebase console](https://console.firebase.google.com), create a project, then
     **Build → Firestore Database → Create database** (any region, production mode is fine).
   - **Project settings (⚙️) → Service accounts → Generate new private key** downloads a JSON file.
   - Open that file, copy its *entire contents as one line*, and set it as the `FIREBASE_CREDENTIALS_JSON`
     environment variable. Each account's settings are then stored in their own Firestore document, so
     nothing depends on Render's disk or on your Saved Messages.
   - If you skip this, each account automatically falls back to the original behaviour: settings saved in
     that account's own Saved Messages. You can add Firebase later — the first connection after that
     migrates the existing settings into Firestore automatically.
5. **GitHub** — push this folder to a *private* repository (`.env` is git-ignored).
6. **Render** — *New → Blueprint* → pick the repo (it reads `render.yaml`, plan *Free*), then fill in
   `API_ID`, `API_HASH`, `TELEGRAM_SESSION` or `TELEGRAM_SESSIONS`, `BOT_TOKEN` (and optionally
   `GROQ_API_KEY`, `FIREBASE_CREDENTIALS_JSON`, `TIMEZONE`) → *Apply*.
7. When the log shows each account coming online, open your panel bot in Telegram and send `/start`. With
   more than one account you'll see a switcher first; only you get the panel.

### A note on multiple accounts

This project only ever automates accounts whose session string *you* provide — there's no way for it to
control an account you don't already have the login for. Running several of your own accounts from one
deployment is fine; each one still only obeys its own outgoing messages, exactly like the single-account
version. Keep in mind Telegram's terms of service still apply to each account individually, and that more
accounts means more RAM — Render's free plan has limited memory, so test with a couple of accounts before
adding many.

### Free-tier facts you should know
- **Sleeping:** Render spins a free web service down after 15 minutes without inbound traffic. A sleeping
  userbot is an offline userbot. `KEEPALIVE=1` (default) makes the bot ping its own public URL every 10 minutes;
  you can also use an external pinger on `/healthz`. Render staff have said deliberately keeping free services awake
  goes against the spirit of the free tier, so this could stop working — a paid instance is the reliable option.
- **750 free hours/month** per workspace ≈ one always-on service. Don't run other free services alongside it.
- **Settings survive restarts.** With `FIREBASE_CREDENTIALS_JSON` set, each account's settings live in its
  own Firestore document. Without it, they fall back to one message (starting with `runak-store:v1`) in that
  account's own *Saved Messages* — please don't delete it in that case.
- **One session, one place.** Never run the same session string (from `TELEGRAM_SESSION`/`TELEGRAM_SESSIONS`)
  locally and on Render at the same time — Telegram will invalidate it.
- Restarting from the panel briefly logs the panel bot in again; avoid restart loops.

## Environment variables

| Name | Required | Notes |
|---|---|---|
| `API_ID`, `API_HASH` | ✅ | from my.telegram.org — shared by every account |
| `TELEGRAM_SESSION` or `TELEGRAM_SESSIONS` | ✅ | one session string, or several comma-separated, from `create_session.py` |
| `BOT_TOKEN` | recommended | panel bot; without it the userbot(s) run with no panel |
| `OWNER_ID` | optional | your numeric Telegram user id, only needed if you'll message the panel bot from an account that isn't one of the automated ones |
| `FIREBASE_CREDENTIALS_JSON` | optional | Firebase service-account JSON, pasted as one line; enables Firestore storage |
| `GOOGLE_APPLICATION_CREDENTIALS` | optional | alternative to the above: a path to that JSON file |
| `GROQ_API_KEY` | optional | enables the AI plugin |
| `OWNER_USERNAME` | optional | your Telegram username (no @) — enables the 👑 Owner button on `/start` |
| `UPDATE_URL` | optional | link for the 📢 Update button on `/start` (e.g. your channel) |
| `OPEN_ACCESS` | optional | `1` lets anyone use the bot; default `0` = only you and people you `.auth` |
| `START_MEDIA` | optional | https URL of a photo/video shown on the `/start` card |
| `VAULT_KEY` | for public login | secret that encrypts hosted users' sessions (needs Firebase too). Generate: `python -c "import secrets;print(secrets.token_urlsafe(32))"`. Don't lose it — sessions can't be decrypted without it |
| `MAX_HOSTED` | optional | cap on users who can log in through the bot (default 25) |
| `HOSTED_LOG_CHAT` | optional | chat id or @username that gets a "New Userbot Hosted" card |
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
