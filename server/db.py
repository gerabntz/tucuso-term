import sqlite3
from pathlib import Path

from flask import current_app, g

REPO_ROOT = Path(__file__).parents[1]
MIGRATIONS = REPO_ROOT / "data" / "migrations"


def get_db():
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE"])
    return g.db


def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def apply_migrations(conn):
    for sql in sorted(MIGRATIONS.glob("*.sql")):
        conn.executescript(sql.read_text())
    conn.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
