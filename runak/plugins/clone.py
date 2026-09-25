"""Clone another Telegram user's profile and restore the original profile later."""
import json
import logging
import os
import tempfile

from telethon.tl import functions
from telethon.tl.functions.users import GetFullUserRequest

from ..context import say

NAME = "clone"
TITLE = "👥 Profile Clone"
DESC = "Temporarily clone a user's name, bio, and profile photo."
DEFAULT_ON = False
COMMANDS = [
    ("clone <username/userid>", "Clone a user's profile (or reply to a user)"),
    ("revert", "Restore the profile saved before cloning"),
]

log = logging.getLogger("runak.plugins.clone")
BACKUP_DIR = os.path.join("DB", "profile_backups")


def _backup_path(ctx) -> str:
    # Include the account id so multiple accounts never share a backup.
    return os.path.join(BACKUP_DIR, f"{ctx.me.id}.json")


def _temporary_path(suffix=".jpg") -> str:
    fd, path = tempfile.mkstemp(prefix="runak-clone-", suffix=suffix)
    os.close(fd)
    return path


async def _download_photo(client, entity, path):
    """Download a photo and return its actual path, or None if there is no photo."""
    downloaded = await client.download_profile_photo(entity, file=path)
    return downloaded if downloaded and os.path.exists(downloaded) else None


async def _upload_photo(client, path):
    with open(path, "rb") as photo:
        uploaded = await client.upload_file(photo)
    await client(functions.photos.UploadProfilePhotoRequest(file=uploaded))


async def _target_from_event(ctx, event, arg):
    if arg:
        return await ctx.client.get_entity(arg)
    reply = await event.get_reply_message()
    if reply:
        return await reply.get_sender()
    return None


def setup(ctx):
    @ctx.command(NAME, "clone")
    async def clone(event, arg):
        target = None
        temporary_photo = None
        try:
            target = await _target_from_event(ctx, event, arg)
            if target is None:
                await say(event, "❌ Reply to a user or provide a username/user ID.", md=False)
                return
            if getattr(target, "id", None) == ctx.me.id:
                await say(event, "❌ You cannot clone your own profile.", md=False)
                return

            full_user = await ctx.client(GetFullUserRequest(target))
            os.makedirs(BACKUP_DIR, exist_ok=True)
            backup_file = _backup_path(ctx)

            # Never overwrite the original backup: a second clone must still be
            # reversible to the profile from before the first clone.
            if not os.path.exists(backup_file):
                original_photo = _temporary_path()
                try:
                    original_photo = await _download_photo(ctx.client, "me", original_photo)
                    backup = {
                        "first_name": ctx.me.first_name or "",
                        "last_name": ctx.me.last_name or "",
                        "about": (await ctx.client(GetFullUserRequest(ctx.me))).full_user.about or "",
                        "photo_path": original_photo,
                    }
                    with open(backup_file, "w", encoding="utf-8") as file:
                        json.dump(backup, file)
                except Exception:
                    if original_photo and os.path.exists(original_photo):
                        os.remove(original_photo)
                    raise

            temporary_photo = _temporary_path()
            temporary_photo = await _download_photo(ctx.client, target, temporary_photo)

            await ctx.client(functions.account.UpdateProfileRequest(
                first_name=(target.first_name or "")[:64],
                last_name=(target.last_name or "")[:64],
                about=((full_user.full_user.about if full_user.full_user else "") or "")[:70],
            ))
            if temporary_photo:
                await _upload_photo(ctx.client, temporary_photo)

            await say(event, "👥 Profile successfully cloned!", md=False)
        except Exception as exc:
            log.exception("Profile clone failed")
            await say(event, f"❌ Clone failed: {exc}", md=False)
        finally:
            if temporary_photo and os.path.exists(temporary_photo):
                os.remove(temporary_photo)

    @ctx.command(NAME, "revert")
    async def revert(event, arg):
        backup_file = _backup_path(ctx)
        if not os.path.exists(backup_file):
            await say(event, "❌ No backup found. Clone a profile first.", md=False)
            return

        try:
            with open(backup_file, encoding="utf-8") as file:
                backup = json.load(file)

            await ctx.client(functions.account.UpdateProfileRequest(
                first_name=backup.get("first_name", "")[:64],
                last_name=backup.get("last_name", "")[:64],
                about=backup.get("about", "")[:70],
            ))

            # Upload the saved photo without deleting current or previous photos.
            # Telegram keeps uploaded profile photos in the account's photo history.
            photo_path = backup.get("photo_path")
            if photo_path and os.path.exists(photo_path):
                await _upload_photo(ctx.client, photo_path)

            # Only remove the backup after every restore operation succeeds, so
            # a failed photo restore can be retried instead of losing the backup.
            os.remove(backup_file)
            if photo_path and os.path.exists(photo_path):
                os.remove(photo_path)
            await say(event, "🔄 Profile successfully reverted!", md=False)
        except Exception as exc:
            log.exception("Profile revert failed")
            await say(event, f"❌ Revert failed: {exc}", md=False)
