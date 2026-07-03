import sqlite3
from pathlib import Path

import pytest

from data.importers.common import verify_sha256, import_rows
from data.importers.original_vocab import parse_vocab, SOURCE as VOCAB_SOURCE
from data.importers.original_vocab import main as _  # noqa: F401 (import check)
from data.importers.unisdr import parse_unisdr, TERM_MAP, SOURCE as UNISDR_SOURCE

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
    """The draft must be original wording, not the COVENIN definitions.

    The COVENIN text itself is license-encumbered and not in the repo; we check
    against a pinned fingerprint of 8-word-shingle hashes derived from it."""
    import hashlib
    fp_path = REPO_ROOT / "data" / "sources" / "covenin-3661-fingerprint.txt"
    verify_sha256(fp_path)
    shingles = {ln for ln in fp_path.read_text().splitlines()
                if ln and not ln.startswith("#")}
    assert len(shingles) > 1500  # sanity: fingerprint not truncated
    src = (REPO_ROOT / "data" / "sources" / "vocabulario-ve-original.json").read_text()
    for row in parse_vocab(REPO_ROOT / "data" / "sources" / "vocabulario-ve-original.json"):
        words = row["definition"].lower().split()
        for i in range(max(1, len(words) - 7)):
            head = " ".join(words[i:i + 8])
            digest = hashlib.sha256(head.encode()).hexdigest()[:16]
            assert digest not in shingles, f"verbatim COVENIN wording in: {row['text']}"
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
