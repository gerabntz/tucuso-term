import sqlite3
from pathlib import Path

import pytest

from data.importers.covenin import verify_sha256
from data.importers.original_vocab import parse_vocab, SOURCE as VOCAB_SOURCE
from data.importers.original_vocab import main as _  # noqa: F401 (import check)
from data.importers.unisdr import parse_unisdr, TERM_MAP, SOURCE as UNISDR_SOURCE
from data.importers.covenin import import_rows

REPO_ROOT = Path(__file__).parents[1]


@pytest.fixture
def db_path(tmp_path):
    db_file = tmp_path / "t.db"
    conn = sqlite3.connect(str(db_file))
    for m in sorted((REPO_ROOT / "data" / "migrations").glob("*.sql")):
        conn.executescript(m.read_text())
    conn.commit()
    conn.close()
    return str(db_file)


def test_original_vocab_pinned_and_complete(db_path):
    src = REPO_ROOT / "data" / "sources" / "vocabulario-ve-original.json"
    verify_sha256(src)
    rows = parse_vocab(src)
    assert len(rows) >= 40
    assert all(r["en_equiv"] and r["definition"] and r["example"] for r in rows)
    import_rows(db_path, rows, VOCAB_SOURCE)
    conn = sqlite3.connect(db_path)
    n = conn.execute("SELECT COUNT(*) FROM seed_staging WHERE source=?"
                     " AND en_equiv IS NOT NULL", (VOCAB_SOURCE,)).fetchone()[0]
    assert n == len(rows)
    conn.close()


def test_original_vocab_is_not_covenin_text():
    """The draft must be original wording, not the COVENIN definitions."""
    src = (REPO_ROOT / "data" / "sources" / "vocabulario-ve-original.json").read_text()
    covenin = (REPO_ROOT / "data" / "sources" / "covenin-3661-2001.txt").read_text()
    covenin_flat = " ".join(covenin.split()).lower()
    for row in parse_vocab(REPO_ROOT / "data" / "sources" / "vocabulario-ve-original.json"):
        # no definition sentence may appear verbatim in the COVENIN text
        head = " ".join(row["definition"].split()[:8]).lower()
        assert head not in covenin_flat, f"verbatim COVENIN wording in: {row['text']}"
    assert "PDVSA" not in src


def test_unisdr_parse_and_pairs(db_path):
    src = REPO_ROOT / "data" / "sources" / "unisdr-terminology-2009-es.txt"
    verify_sha256(src)
    entries = parse_unisdr(src)
    assert len(entries) >= 45
    es_terms = {e[0] for e in entries}
    for must in ("Desastre", "Amenaza", "Resiliencia", "Vulnerabilidad",
                 "Sistema de alerta temprana", "Preparación", "Respuesta"):
        assert must in es_terms
    for es, en, definition in entries:
        assert en == TERM_MAP.get(es) or en == TERM_MAP.get(es + "*") or en
        assert len(definition) > 40, f"suspiciously short definition for {es}"
        assert "©" not in definition and "www." not in definition
    import_rows(db_path, [dict(source_ref=None, text=e, definition=d, en_equiv=n,
                               example=None) for e, n, d in
                          [(a, b, c) for a, b, c in entries]], UNISDR_SOURCE)
    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM seed_staging WHERE source=?",
                        (UNISDR_SOURCE,)).fetchone()[0] == len(entries)
    conn.close()
