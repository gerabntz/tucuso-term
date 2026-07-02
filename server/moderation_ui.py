"""Moderation queue UI (T9, F4). Every vote goes through cast_vote —
the same deterministic quorum the tests pin down (M1/M3).
"""
import json

from flask import Blueprint, g, redirect, render_template, request, url_for

from server.auth import consume_magic_link, login_reviewer, require_reviewer
from server.db import get_db
from server.moderation import DuplicateVote, VoteError, cast_vote

bp_mod = Blueprint("mod", __name__, url_prefix="/mod")


@bp_mod.get("/login/<token>")
def login(token):
    rid = consume_magic_link(get_db(), token)
    if rid is None:
        return "Enlace inválido, usado o expirado. Pida uno nuevo.", 403
    login_reviewer(rid)
    return redirect(url_for("mod.queue"))


@bp_mod.get("/queue")
@require_reviewer
def queue():
    db = get_db()
    terms = db.execute(
        "SELECT * FROM terms WHERE status='pending_review' ORDER BY id"
    ).fetchall()
    revisions = [dict(r, proposed=json.loads(r["proposed_fields"]),
                      base=db.execute("SELECT text, lang FROM terms WHERE id=?",
                                      (r["term_id"],)).fetchone())
                 for r in db.execute(
                     "SELECT * FROM revisions WHERE status='pending_review' ORDER BY id"
                 ).fetchall()]
    my_votes = {(v["target_type"], v["target_id"]) for v in db.execute(
        "SELECT target_type, target_id FROM approvals WHERE reviewer_id=?",
        (g.reviewer_id,)).fetchall()}
    return render_template("mod_queue.html", terms=terms, revisions=revisions,
                           my_votes=my_votes, message=request.args.get("m"))


@bp_mod.post("/vote")
@require_reviewer
def vote():
    f = request.form
    try:
        status = cast_vote(get_db(), f.get("target_type"),
                           int(f.get("target_id", 0)), g.reviewer_id,
                           f.get("verdict"), f.get("reason") or None)
        msg = f"Voto registrado — estado: {status}"
    except DuplicateVote:
        msg = "Ya votó sobre este elemento."
    except (VoteError, ValueError) as exc:
        msg = f"Voto rechazado: {exc}"
    return redirect(url_for("mod.queue", m=msg))
