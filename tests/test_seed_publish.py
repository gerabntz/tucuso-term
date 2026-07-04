import sqlite3
from pathlib import Path

import pytest

from server.seed_publish import publish_seeds

REPO_ROOT = Path(__file__).parents[1]


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(str(tmp_path / "t.db"))
    c.row_factory = sqlite3.Row
    for m in sorted((REPO_ROOT / "data" / "migrations").glob("*.sql")):
        c.executescript(m.read_text())
    c.executemany(
        "INSERT INTO seed_staging (source, text, definition, category,"
        " register, en_equiv, example) VALUES (?,?,?,?,?,?,?)",
        [("test-src", "réplica", "Sismo menor posterior.", "Protocolos",
          "formal", "aftershock", "Hubo tres réplicas."),
         ("test-src", "damnificado", "Persona afectada.", "Refugios",
          "formal", None, None)])
    c.commit()
    yield c
    c.close()


def test_publish_creates_concept_pairs(conn):
    published, skipped = publish_seeds(conn)
    assert (published, skipped) == (2, 0)
    es = conn.execute("SELECT * FROM terms WHERE text='réplica'").fetchone()
    en = conn.execute("SELECT * FROM terms WHERE text='aftershock'").fetchone()
    assert es["status"] == en["status"] == "published"
    assert es["concept_id"] == en["concept_id"]
    assert es["definition"] == "Sismo menor posterior."
    assert en["lang"] == "en"
    # row without en_equiv publishes solo
    solo = conn.execute(
        "SELECT COUNT(*) FROM terms WHERE concept_id = (SELECT concept_id"
        " FROM terms WHERE text='damnificado')").fetchone()[0]
    assert solo == 1


def test_publish_is_idempotent(conn):
    publish_seeds(conn)
    published, skipped = publish_seeds(conn)
    assert (published, skipped) == (0, 2)
    assert conn.execute("SELECT COUNT(*) FROM terms").fetchone()[0] == 3


def test_dry_run_writes_nothing(conn, capsys):
    published, _ = publish_seeds(conn, dry_run=True)
    assert published == 2
    assert conn.execute("SELECT COUNT(*) FROM terms").fetchone()[0] == 0
    assert "réplica ⇄ aftershock" in capsys.readouterr().out


def test_definition_is_searchable(conn):
    publish_seeds(conn)
    hits = conn.execute(
        "SELECT t.text FROM terms_fts f JOIN terms t ON t.id = f.rowid"
        " WHERE terms_fts MATCH 'sismo'").fetchall()
    assert [h["text"] for h in hits] == ["réplica"]
