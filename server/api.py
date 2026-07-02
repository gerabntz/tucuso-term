"""Public JSON API (F1–F3). Deliberately has NO update/delete endpoints for
terms (N5/M8) — corrections travel as revisions through the quorum.

Moderation voting is exposed only through server-side reviewer auth (T9);
this blueprint contains no /vote route on purpose.
"""
import uuid

from flask import Blueprint, current_app, jsonify, request

from server import ratelimit, tokens
from server.db import get_db
from server.moderation import current_published
from server.quorum import PENDING

bp = Blueprint("api", __name__, url_prefix="/api")

CATEGORIES = {"Médico", "Construcción/Rescate", "Refugios", "Servicios",
              "Clima", "Modismos", "Protocolos"}


def public_term(row):
    """Serialize a term for readers — timestamps coarsened to the day (M9)."""
    return {
        "id": row["id"],
        "concept_id": row["concept_id"],
        "lang": row["lang"],
        "text": row["text"],
        "category": row["category"],
        "register": row["register"],
        "zone": row["zone"],
        "example": row["example"],
        "source": row["source"],
        "status": row["status"],
        "date": (row["created_at"] or "")[:10],
    }


def _throttled(db):
    key = current_app.config["SECRET_KEY"]
    return not ratelimit.check_and_record(db, request.remote_addr or "?", key)


@bp.get("/terms/<int:term_id>")
def get_term(term_id):
    db = get_db()
    row = db.execute(
        "SELECT * FROM terms WHERE id=? AND status='published'", (term_id,)
    ).fetchone()
    if row is None:
        return jsonify(error="not found"), 404
    return jsonify(public_term(row))


@bp.post("/terms")
def submit_term():
    payload = request.get_json(silent=True) or {}
    if payload.get("website"):  # honeypot field — bots fill it, humans never see it
        return jsonify(error="rejected"), 400
    missing = [f for f in ("text", "lang", "category") if not payload.get(f)]
    if missing:
        return jsonify(error=f"missing fields: {missing}"), 400
    if payload["category"] not in CATEGORIES:
        return jsonify(error="unknown category"), 400
    if payload["lang"] not in ("es", "en"):
        return jsonify(error="MVP languages are es/en"), 400

    db = get_db()
    if _throttled(db):
        return jsonify(error="too many submissions, try later"), 429

    with db:
        cur = db.execute(
            "INSERT INTO terms (concept_id, lang, text, category, register, zone,"
            " example, source, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (payload.get("concept_id") or uuid.uuid4().hex,
             payload["lang"], payload["text"], payload["category"],
             payload.get("register", "neutral"), payload.get("zone"),
             payload.get("example"), payload.get("source", "community"),
             PENDING),
        )
        token = tokens.issue(db, "term", cur.lastrowid)
    return jsonify(status=PENDING, token=token), 201


@bp.post("/terms/<int:term_id>/revisions")
def suggest_correction(term_id):
    payload = request.get_json(silent=True) or {}
    if payload.get("website"):
        return jsonify(error="rejected"), 400
    proposed = payload.get("proposed_fields")
    reason = payload.get("reason")
    if not isinstance(proposed, dict) or not proposed or not reason:
        return jsonify(error="proposed_fields (object) and reason are required"), 400

    db = get_db()
    base = db.execute(
        "SELECT id FROM terms WHERE id=? AND status='published'", (term_id,)
    ).fetchone()
    if base is None:
        return jsonify(error="not found"), 404
    if _throttled(db):
        return jsonify(error="too many submissions, try later"), 429

    import json as _json
    with db:
        cur = db.execute(
            "INSERT INTO revisions (term_id, proposed_fields, reason, status)"
            " VALUES (?, ?, ?, ?)",
            (term_id, _json.dumps(proposed), reason, PENDING),
        )
        token = tokens.issue(db, "revision", cur.lastrowid)
    return jsonify(status=PENDING, token=token), 201


@bp.get("/status/<token>")
def submission_status(token):
    db = get_db()
    with db:
        row = tokens.lookup(db, token)
    if row is None:
        return jsonify(error="unknown or expired token"), 404
    table = "terms" if row["target_type"] == "term" else "revisions"
    target = db.execute(
        f"SELECT status FROM {table} WHERE id=?", (row["target_id"],)
    ).fetchone()
    if target is None:
        return jsonify(error="unknown or expired token"), 404
    return jsonify(target_type=row["target_type"], status=target["status"])


@bp.get("/concepts/<concept_id>")
def get_concept(concept_id):
    """Live published version per language, plus how many versions exist."""
    db = get_db()
    out = {}
    for lang in ("es", "en"):
        row = current_published(db, concept_id, lang)
        if row:
            versions = db.execute(
                "SELECT COUNT(*) FROM terms WHERE concept_id=? AND lang=?"
                " AND status='published'", (concept_id, lang),
            ).fetchone()[0]
            entry = public_term(row)
            entry["versions"] = versions
            out[lang] = entry
    if not out:
        return jsonify(error="not found"), 404
    return jsonify(out)
