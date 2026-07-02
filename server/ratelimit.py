"""Submission rate limiting (F2) without storing IPs (M9).

The client address is hashed with a salt that rotates daily, so even the
hashes cannot be correlated across days. Events older than RETENTION_HOURS
are purged on every check — short retention is the feature, not a cost.
"""
import hashlib
from datetime import datetime, timedelta, timezone

MAX_PER_WINDOW = 10
WINDOW_MINUTES = 60
RETENTION_HOURS = 24


def _daily_salt(secret_key):
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"{secret_key}:{day}"


def ip_hash(remote_addr, secret_key):
    material = f"{_daily_salt(secret_key)}:{remote_addr}".encode()
    return hashlib.sha256(material).hexdigest()


def check_and_record(conn, remote_addr, secret_key):
    """True if the submission is allowed (and recorded), False if throttled."""
    now = datetime.now(timezone.utc)
    conn.execute(
        "DELETE FROM rate_events WHERE created_at < ?",
        ((now - timedelta(hours=RETENTION_HOURS)).isoformat(),),
    )
    h = ip_hash(remote_addr, secret_key)
    window_start = (now - timedelta(minutes=WINDOW_MINUTES)).isoformat()
    count = conn.execute(
        "SELECT COUNT(*) FROM rate_events WHERE ip_hash=? AND created_at >= ?",
        (h, window_start),
    ).fetchone()[0]
    if count >= MAX_PER_WINDOW:
        return False
    conn.execute(
        "INSERT INTO rate_events (ip_hash, created_at) VALUES (?, ?)",
        (h, now.isoformat()),
    )
    return True
