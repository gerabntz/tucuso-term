"""Search endpoint (F1): FTS5, accent-insensitive, bidirectional (T6)."""
import re
import unicodedata

from flask import Blueprint, jsonify, request

from server.api import public_term
from server.db import get_db

bp_search = Blueprint("search", __name__, url_prefix="/api")

FILTERS = ("lang", "category", "register", "zone")


def deaccent(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def build_match(q):
    tokens = re.sub(r"[^\w\s]", " ", q, flags=re.UNICODE).split()
    if not tokens:
        return None
    plain = " ".join(f"{t}*" for t in tokens)
    flat = deaccent(" ".join(tokens))
    if flat != " ".join(tokens):
        flat_expr = " ".join(f"{t}*" for t in flat.split())
        return f"({plain}) OR ({flat_expr})"
    return plain


@bp_search.get("/search")
def search():
    q = (request.args.get("q") or "").strip()
    if not q or len(q) > 100:
        return jsonify(error="q is required (max 100 chars)"), 400
    match = build_match(q)
    if match is None:
        return jsonify(error="query has no searchable characters"), 400
    try:
        limit = min(max(int(request.args.get("limit", 20)), 1), 50)
    except ValueError:
        limit = 20

    sql = ("SELECT t.* FROM terms_fts f JOIN terms t ON t.id = f.rowid"
           " WHERE terms_fts MATCH ? AND t.status='published'")
    params = [match]
    for f in FILTERS:
        v = request.args.get(f)
        if v:
            sql += f" AND t.{f} = ?"
            params.append(v)
    sql += " ORDER BY bm25(terms_fts) LIMIT ?"
    params.append(limit)

    db = get_db()
    results = []
    for row in db.execute(sql, params).fetchall():
        d = public_term(row)
        d["counterparts"] = [
            public_term(r) for r in db.execute(
                "SELECT * FROM terms WHERE concept_id=? AND lang<>?"
                " AND status='published' ORDER BY id DESC",
                (row["concept_id"], row["lang"]),
            ).fetchall()
        ]
        results.append(d)
    return jsonify(query=q, results=results)
