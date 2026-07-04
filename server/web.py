"""Server-rendered pages (T7/T8). Forms work without JavaScript — the
JSON API and these routes share the same underlying flows.
"""
import json
import uuid

from flask import Blueprint, current_app, render_template, request

from server import ratelimit, tokens
from server.api import CATEGORIES, LANGS, public_term
from server.db import get_db
from server.quorum import PENDING
from server.search import build_match

bp_web = Blueprint("web", __name__)

CATEGORY_LIST = sorted(CATEGORIES)


def _throttled(db):
    key = current_app.config["SECRET_KEY"]
    return not ratelimit.check_and_record(db, request.remote_addr or "?", key)


@bp_web.get("/")
def index():
    q = (request.args.get("q") or "").strip()
    category = request.args.get("category") or ""
    results = []
    if q and len(q) <= 100:
        match = build_match(q)
        if match:
            db = get_db()
            sql = ("SELECT t.* FROM terms_fts f JOIN terms t ON t.id = f.rowid"
                   " WHERE terms_fts MATCH ? AND t.status='published'")
            params = [match]
            if category:
                sql += " AND t.category = ?"
                params.append(category)
            sql += " ORDER BY bm25(terms_fts) LIMIT 20"
            for row in db.execute(sql, params).fetchall():
                d = public_term(row)
                d["counterparts"] = [public_term(r) for r in db.execute(
                    "SELECT * FROM terms WHERE concept_id=? AND lang<>?"
                    " AND status='published' ORDER BY id DESC",
                    (row["concept_id"], row["lang"])).fetchall()]
                results.append(d)
    return render_template("index.html", q=q, category=category,
                           categories=CATEGORY_LIST, results=results)


@bp_web.get("/term/<int:term_id>")
def term_detail(term_id):
    db = get_db()
    row = db.execute(
        "SELECT * FROM terms WHERE id=? AND status='published'", (term_id,)
    ).fetchone()
    if row is None:
        return render_template("index.html", q="", category="",
                               categories=CATEGORY_LIST, results=[]), 404
    counterparts = [public_term(r) for r in db.execute(
        "SELECT * FROM terms WHERE concept_id=? AND lang<>? AND status='published'"
        " ORDER BY id DESC", (row["concept_id"], row["lang"])).fetchall()]
    versions = db.execute(
        "SELECT COUNT(*) FROM terms WHERE concept_id=? AND lang=? AND status='published'",
        (row["concept_id"], row["lang"])).fetchone()[0]
    return render_template("term.html", term=public_term(row),
                           counterparts=counterparts, versions=versions)


@bp_web.route("/submit", methods=["GET", "POST"])
def submit():
    token = error = None
    if request.method == "POST":
        f = request.form
        db = get_db()
        if f.get("website"):
            error = "Envío rechazado."
        elif not f.get("text") or f.get("category") not in CATEGORIES \
                or f.get("lang") not in LANGS:
            error = "Faltan campos obligatorios."
        elif _throttled(db):
            error = "Demasiados envíos, intente más tarde."
        else:
            with db:
                cur = db.execute(
                    "INSERT INTO terms (concept_id, lang, text, definition,"
                    " category, subdomain, register, zone, variations,"
                    " contrast_note, ling_info, example, source, status)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (uuid.uuid4().hex, f["lang"], f["text"].strip(),
                     f.get("definition") or None,
                     f["category"], f.get("subdomain") or None,
                     f.get("register", "neutral"), f.get("zone") or None,
                     f.get("variations") or None,
                     f.get("contrast_note") or None,
                     f.get("ling_info") or None, f.get("example") or None,
                     "community", PENDING))
                token = tokens.issue(db, "term", cur.lastrowid)
    return render_template("submit.html", categories=CATEGORY_LIST,
                           token=token, error=error)


@bp_web.route("/term/<int:term_id>/revise", methods=["GET", "POST"])
def revise(term_id):
    db = get_db()
    row = db.execute(
        "SELECT * FROM terms WHERE id=? AND status='published'", (term_id,)
    ).fetchone()
    if row is None:
        return render_template("index.html", q="", category="",
                               categories=CATEGORY_LIST, results=[]), 404
    token = error = None
    if request.method == "POST":
        f = request.form
        proposed = {}
        for field in ("text", "example"):
            v = (f.get(field) or "").strip()
            if v and v != (row[field] or ""):
                proposed[field] = v
        if f.get("website"):
            error = "Envío rechazado."
        elif not f.get("reason") or not proposed:
            error = "Indique el cambio y el motivo."
        elif _throttled(db):
            error = "Demasiados envíos, intente más tarde."
        else:
            with db:
                cur = db.execute(
                    "INSERT INTO revisions (term_id, proposed_fields, reason, status)"
                    " VALUES (?,?,?,?)",
                    (term_id, json.dumps(proposed), f["reason"].strip(), PENDING))
                token = tokens.issue(db, "revision", cur.lastrowid)
    return render_template("revise.html", term=public_term(row),
                           token=token, error=error)


@bp_web.get("/guardados")
def saved():
    """Favorites/history shell — content lives in localStorage, client-side
    only (M4/M9: the server never sees what anyone saves or reads)."""
    return render_template("saved.html")


@bp_web.get("/install")
def install():
    return render_template("install.html")


@bp_web.get("/status")
def status():
    token = (request.args.get("token") or "").strip()
    st = None
    if token:
        db = get_db()
        with db:
            row = tokens.lookup(db, token)
        if row:
            table = "terms" if row["target_type"] == "term" else "revisions"
            target = db.execute(
                f"SELECT status FROM {table} WHERE id=?", (row["target_id"],)
            ).fetchone()
            st = target["status"] if target else None
    return render_template("status.html", token=token, status=st)
