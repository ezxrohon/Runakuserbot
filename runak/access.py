"""Who may use the bot (/start, /help, /login).

Admins = your own accounts (and OWNER_ID). Anyone an admin has run `.auth @username` for is allowed
too. Everyone else sees the "not authorized" card. Set OPEN_ACCESS=1 to make the bot public.
Hosted users' accounts are never admins, so their own `.auth` lists grant nothing here.
"""
from . import config as cfg

_admin_ctxs: list = []


def init(ctxs: list) -> None:
    """`ctxs` is the live list of the owner's own accounts (not hosted users)."""
    global _admin_ctxs
    _admin_ctxs = ctxs


def is_admin(user_id) -> bool:
    return user_id is not None and (user_id == cfg.OWNER_ID or any(c.me.id == user_id for c in _admin_ctxs))


def allowed(user_id) -> bool:
    if cfg.OPEN_ACCESS or is_admin(user_id):
        return True
    return any(c.is_authorized(user_id) for c in _admin_ctxs)
