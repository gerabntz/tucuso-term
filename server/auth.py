"""Reviewer authentication (T9, M10): invite-only + single-use magic links.

There is no signup route and no password. The operator invites a reviewer via
the CLI, hands them a magic link out-of-band, and the link is dead after one
use or 15 minutes, whichever comes first.
"""
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import g, session

LINK_TTL_MINUTES = 15


def invite_reviewer(conn, handle):
    with conn:
        cur = conn.execute("INSERT INTO reviewers (handle) VALUES (?)", (handle,))
    return cur.lastrowid


def issue_magic_link(conn, handle):
    row = conn.execute(
        "SELECT id FROM reviewers WHERE handle=? AND active=1", (handle,)
    ).fetchone()
    if row is None:
        raise ValueError(f"no active reviewer with handle {handle!r}")
    token = secrets.token_urlsafe(24)
    expires = datetime.now(timezone.utc) + timedelta(minutes=LINK_TTL_MINUTES)
    with conn:
        conn.execute(
            "INSERT INTO magic_links (token, reviewer_id, expires_at) VALUES (?,?,?)",
            (token, row["id"], expires.isoformat()))
    return token


def consume_magic_link(conn, token):
    """Return reviewer_id if the link is live; burn it either way. None if invalid."""
    now = datetime.now(timezone.utc).isoformat()
    with conn:
        row = conn.execute(
            "SELECT reviewer_id, expires_at, used_at FROM magic_links WHERE token=?",
            (token,)).fetchone()
        if row is None or row["used_at"] is not None or row["expires_at"] < now:
            return None
        conn.execute(
            "UPDATE magic_links SET used_at=? WHERE token=? AND used_at IS NULL",
            (now, token))
        active = conn.execute(
            "SELECT 1 FROM reviewers WHERE id=? AND active=1",
            (row["reviewer_id"],)).fetchone()
    return row["reviewer_id"] if active else None


def login_reviewer(reviewer_id):
    session.clear()
    session["reviewer_id"] = reviewer_id


def require_reviewer(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        rid = session.get("reviewer_id")
        if not rid:
            return "No autorizado", 401
        g.reviewer_id = rid
        return view(*args, **kwargs)
    return wrapped
