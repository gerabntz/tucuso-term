import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from server.db import apply_migrations
from server.moderation import DuplicateVote, VoteError, cast_vote, current_published
from server.quorum import PENDING, PUBLISHED, REJECTED, resolve
from server import tokens, ratelimit


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    apply_migrations(c)
    yield c
    c.close()


def make_term(conn, status=PENDING, **over):
    fields = dict(concept_id="c1", lang="es", text="aplastamiento",
                  category="Médico", register="formal", source="community",
                  status=status)
    fields.update(over)
    cur = conn.execute(
        "INSERT INTO terms (concept_id, lang, text, category, register, source, status)"
        " VALUES (:concept_id, :lang, :text, :category, :register, :source, :status)",
        fields)
    conn.commit()
    return cur.lastrowid


# --- quorum function ---

def test_resolve_pending_then_published():
    assert resolve([]) == PENDING
    assert resolve([(1, "approve")]) == PENDING
    assert resolve([(1, "approve"), (2, "approve")]) == PUBLISHED


def test_resolve_veto_always_rejects():
    assert resolve([(1, "approve"), (2, "approve"), (3, "veto")]) == REJECTED
    assert resolve([(3, "veto")]) == REJECTED


def test_resolve_same_reviewer_does_not_double_count():
    assert resolve([(1, "approve"), (1, "approve")]) == PENDING


# --- state machine over the DB ---

def test_two_distinct_approvals_publish(conn):
    tid = make_term(conn)
    assert cast_vote(conn, "term", tid, 1, "approve") == PENDING
    assert cast_vote(conn, "term", tid, 2, "approve") == PUBLISHED
    row = conn.execute("SELECT status FROM terms WHERE id=?", (tid,)).fetchone()
    assert row["status"] == PUBLISHED


def test_same_reviewer_twice_raises(conn):
    tid = make_term(conn)
    cast_vote(conn, "term", tid, 1, "approve")
    with pytest.raises(DuplicateVote):
        cast_vote(conn, "term", tid, 1, "approve")
    assert conn.execute("SELECT status FROM terms WHERE id=?", (tid,)).fetchone()[0] == PENDING


def test_veto_rejects_and_requires_reason(conn):
    tid = make_term(conn)
    with pytest.raises(VoteError):
        cast_vote(conn, "term", tid, 1, "veto")
    assert cast_vote(conn, "term", tid, 1, "veto", reason="wrong gloss") == REJECTED


def test_cannot_vote_on_published(conn):
    tid = make_term(conn, status=PUBLISHED)
    with pytest.raises(VoteError):
        cast_vote(conn, "term", tid, 1, "approve")


def test_approved_revision_creates_new_row_keeps_history(conn):
    tid = make_term(conn, status=PUBLISHED)
    cur = conn.execute(
        "INSERT INTO revisions (term_id, proposed_fields, reason, status)"
        " VALUES (?, ?, ?, ?)",
        (tid, json.dumps({"text": "síndrome de aplastamiento"}), "más preciso", PENDING))
    rid = cur.lastrowid
    conn.commit()

    cast_vote(conn, "revision", rid, 1, "approve")
    assert cast_vote(conn, "revision", rid, 2, "approve") == PUBLISHED

    rows = conn.execute(
        "SELECT * FROM terms WHERE concept_id='c1' AND lang='es' ORDER BY id").fetchall()
    assert len(rows) == 2                        # history preserved (I2/M8)
    assert rows[0]["text"] == "aplastamiento"    # original untouched
    live = current_published(conn, "c1", "es")
    assert live["text"] == "síndrome de aplastamiento"


def test_revision_with_forbidden_field_blocked(conn):
    tid = make_term(conn, status=PUBLISHED)
    cur = conn.execute(
        "INSERT INTO revisions (term_id, proposed_fields, reason, status)"
        " VALUES (?, ?, ?, ?)",
        (tid, json.dumps({"status": "published"}), "sneaky", PENDING))
    conn.commit()
    cast_vote(conn, "revision", cur.lastrowid, 1, "approve")
    with pytest.raises(VoteError):
        cast_vote(conn, "revision", cur.lastrowid, 2, "approve")


# --- tokens ---

def test_token_roundtrip_and_expiry(conn):
    tid = make_term(conn)
    tok = tokens.issue(conn, "term", tid)
    assert tokens.lookup(conn, tok)["target_id"] == tid
    conn.execute(
        "UPDATE submission_tokens SET expires_at=? WHERE token=?",
        ((datetime.now(timezone.utc) - timedelta(days=1)).isoformat(), tok))
    assert tokens.lookup(conn, tok) is None      # purged, linkage severed (I3)
    assert conn.execute("SELECT COUNT(*) FROM submission_tokens").fetchone()[0] == 0


# --- rate limiting ---

def test_rate_limit_blocks_and_stores_no_ip(conn):
    for _ in range(ratelimit.MAX_PER_WINDOW):
        assert ratelimit.check_and_record(conn, "10.1.2.3", "k")
    assert not ratelimit.check_and_record(conn, "10.1.2.3", "k")
    assert ratelimit.check_and_record(conn, "10.9.9.9", "k")
    stored = [r[0] for r in conn.execute("SELECT ip_hash FROM rate_events")]
    assert all("10.1.2.3" not in s and "10.9.9.9" not in s for s in stored)
