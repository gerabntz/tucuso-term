"""Expirable submission tokens (M9, C2C transient-token pattern).

A token is the ONLY link between a submitter and their submission — no
account, no IP, no name. Expired tokens are deleted outright (invariant I3:
that deletion is the point), severing the linkage permanently.
"""
import secrets
from datetime import datetime, timedelta, timezone

TOKEN_TTL_DAYS = 30


def issue(conn, target_type, target_id):
    token = secrets.token_urlsafe(24)
    expires = datetime.now(timezone.utc) + timedelta(days=TOKEN_TTL_DAYS)
    conn.execute(
        "INSERT INTO submission_tokens (token, target_type, target_id, expires_at)"
        " VALUES (?, ?, ?, ?)",
        (token, target_type, target_id, expires.isoformat()),
    )
    return token


def lookup(conn, token):
    """Return the (target_type, target_id) row for a live token, else None."""
    purge_expired(conn)
    return conn.execute(
        "SELECT target_type, target_id FROM submission_tokens WHERE token=?",
        (token,),
    ).fetchone()


def purge_expired(conn):
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("DELETE FROM submission_tokens WHERE expires_at < ?", (now,))
