"""Moderation state machine (F4) and revision application (F3, I2, M8).

State flow: pending_review --2 distinct approvals, 0 vetoes--> published
            pending_review --any veto--> rejected (with reason)

Approved revisions are applied by INSERTING a new published term row with the
proposed fields; the previous row is never touched. Reads select the newest
published row per (concept_id, lang); older rows ARE the history.
"""
import json
import sqlite3

from server.quorum import resolve, PENDING, PUBLISHED, REJECTED

REVISABLE_FIELDS = {"text", "category", "register", "zone", "example", "source"}


class DuplicateVote(Exception):
    pass


class VoteError(Exception):
    pass


def cast_vote(conn, target_type, target_id, reviewer_id, verdict, reason=None):
    """Record one reviewer vote and resolve the target's state. Returns new status."""
    if target_type not in ("term", "revision"):
        raise VoteError(f"bad target_type: {target_type}")
    if verdict not in ("approve", "veto"):
        raise VoteError(f"bad verdict: {verdict}")
    if verdict == "veto" and not reason:
        raise VoteError("a veto requires a reason")

    table = "terms" if target_type == "term" else "revisions"
    row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (target_id,)).fetchone()
    if row is None:
        raise VoteError(f"{target_type} {target_id} not found")
    if row["status"] != PENDING:
        raise VoteError(f"{target_type} {target_id} is not pending review")

    try:
        with conn:
            conn.execute(
                "INSERT INTO approvals (target_type, target_id, reviewer_id, verdict, reason)"
                " VALUES (?, ?, ?, ?, ?)",
                (target_type, target_id, reviewer_id, verdict, reason),
            )
            verdicts = conn.execute(
                "SELECT reviewer_id, verdict FROM approvals"
                " WHERE target_type=? AND target_id=?",
                (target_type, target_id),
            ).fetchall()
            status = resolve([(v["reviewer_id"], v["verdict"]) for v in verdicts])
            if status != PENDING:
                conn.execute(
                    f"UPDATE {table} SET status=? WHERE id=? AND status=?",
                    (status, target_id, PENDING),
                )
                if status == PUBLISHED and target_type == "revision":
                    _apply_revision(conn, row)
    except sqlite3.IntegrityError as exc:
        raise DuplicateVote(
            f"reviewer {reviewer_id} already voted on {target_type} {target_id}"
        ) from exc
    return status


def _apply_revision(conn, revision):
    """Insert a NEW published term row carrying the revision's changes (I2)."""
    base = conn.execute(
        "SELECT * FROM terms WHERE id=?", (revision["term_id"],)
    ).fetchone()
    if base is None:
        raise VoteError(f"revision {revision['id']} points at missing term")
    proposed = json.loads(revision["proposed_fields"])
    illegal = set(proposed) - REVISABLE_FIELDS
    if illegal:
        raise VoteError(f"revision proposes non-revisable fields: {sorted(illegal)}")
    fields = {k: base[k] for k in
              ("concept_id", "lang", "text", "category", "register",
               "zone", "example", "audio_ref", "source")}
    fields.update(proposed)
    conn.execute(
        "INSERT INTO terms (concept_id, lang, text, category, register, zone,"
        " example, audio_ref, source, status) VALUES"
        " (:concept_id, :lang, :text, :category, :register, :zone,"
        "  :example, :audio_ref, :source, 'published')",
        fields,
    )


def current_published(conn, concept_id, lang):
    """The live version: newest published row for (concept_id, lang)."""
    return conn.execute(
        "SELECT * FROM terms WHERE concept_id=? AND lang=? AND status='published'"
        " ORDER BY id DESC LIMIT 1",
        (concept_id, lang),
    ).fetchone()
