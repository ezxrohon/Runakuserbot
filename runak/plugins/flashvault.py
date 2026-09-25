"""Safe media utility.

The old implementation silently intercepted view-once media.  This version
only saves media when the account owner explicitly replies with `.saveflash`.
"""
from ..context import say

NAME = "flashvault"
TITLE = "📸 Media Saver"
DESC = "Explicitly save replied media to Saved Messages."
DEFAULT_ON = False
COMMANDS = [("saveflash", "Reply to media and save it to Saved Messages")]


def setup(ctx):
    @ctx.command(NAME, "saveflash")
    async def saveflash(event, arg):
        reply = await event.get_reply_message()
        if not reply or not reply.media:
            await say(event, "❌ Reply to a photo, video, or file.", md=False)
            return
        path = None
        try:
            path = await reply.download_media()
            if not path:
                raise RuntimeError("download returned no file")
            await ctx.client.send_file("me", path, caption="📸 Saved explicitly with .saveflash")
            await say(event, "✅ Media saved to Saved Messages.", md=False)
        except Exception:
            await say(event, "❌ Could not save that media.", md=False)
        finally:
            import os
            if path and os.path.exists(path):
                os.remove(path)
