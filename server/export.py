"""Open dataset export (F6, M7/I5): public, no auth, versioned (T11).

This is the future mobile app's content pipeline and the community's
guarantee against platform lock-in.
"""
import csv
import io
from datetime import datetime, timezone

from flask import Blueprint, Response, jsonify

from server.api import public_term
from server.db import get_db

bp_export = Blueprint("export", __name__, url_prefix="/api/export")

CSV_FIELDS = ["id", "concept_id", "lang", "text", "definition", "category",
              "register", "zone", "example", "source", "date"]


def _published(db):
    return db.execute(
        "SELECT * FROM terms WHERE status='published' ORDER BY id"
    ).fetchall()


def _version(db):
    return db.execute("SELECT COALESCE(MAX(id), 0) FROM terms").fetchone()[0]


def _cached(resp, version):
    resp.headers["Cache-Control"] = "public, max-age=300"
    resp.headers["ETag"] = str(version)
    return resp


@bp_export.get("/terms.json")
def export_json():
    db = get_db()
    version = _version(db)
    payload = {
        "version": version,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "terms": [public_term(r) for r in _published(db)],
    }
    return _cached(jsonify(payload), version)


@bp_export.get("/terms.csv")
def export_csv():
    db = get_db()
    version = _version(db)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for row in _published(db):
        writer.writerow(public_term(row))
    resp = Response(buf.getvalue(), mimetype="text/csv")
    return _cached(resp, version)
