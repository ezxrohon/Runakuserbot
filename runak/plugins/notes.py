from ..context import say

NAME = "notes"
TITLE = "📝 Notes"
DESC = "Save short notes and fetch them anywhere."
DEFAULT_ON = True
COMMANDS = [
    ("save <name> <text>", "Save a note (or reply to a message)"),
    ("get <name>", "Show a note"),
    ("notes", "List your notes"),
    ("clear <name>", "Delete a note"),
]

MAX_NOTES = 50
MAX_LEN = 500  # notes live inside one Saved Messages message, so keep them short


def setup(ctx):
    notes = lambda: ctx.store.data["notes"]  # noqa: E731

    @ctx.command(NAME, "save")
    async def save(event, arg):
        parts = arg.split(maxsplit=1)
        if not parts:
            await say(event, "Usage: `.save <name> <text>` (or reply with `.save <name>`)")
            return
        name = parts[0].lower()[:40]
        text = parts[1] if len(parts) > 1 else ""
        if not text:
            reply = await event.get_reply_message()
            text = (reply.raw_text or "") if reply else ""
        if not text:
            await say(event, "Give me some text to save.")
            return
        if name not in notes() and len(notes()) >= MAX_NOTES:
            await say(event, "❌ Note limit reached. Delete one first.")
            return
        previous = notes().get(name)
        notes()[name] = text[:MAX_LEN]
        if not ctx.store.fits():
            if previous is None:
                notes().pop(name, None)
            else:
                notes()[name] = previous
            await say(event, "❌ Storage is full. Delete a note first.")
            return
        ctx.store.save_soon()
        await say(event, f"📝 Saved note `{name}`.")

    @ctx.command(NAME, "get")
    async def get(event, arg):
        name = arg.lower().strip()
        await say(event, notes().get(name, f"❌ No note named `{name}`."), md=name not in notes())

    @ctx.command(NAME, "notes")
    async def list_notes(event, arg):
        names = sorted(notes())
        await say(event, "📝 **Notes:** " + ", ".join(f"`{n}`" for n in names) if names else "📝 No notes yet.")

    @ctx.command(NAME, "clear")
    async def clear(event, arg):
        name = arg.lower().strip()
        if notes().pop(name, None) is None:
            await say(event, f"❌ No note named `{name}`.")
        else:
            ctx.store.save_soon()
            await say(event, f"🗑 Deleted `{name}`.")
