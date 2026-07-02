import sqlite3
import tempfile
from pathlib import Path

import pytest

from data.importers.covenin import parse_covenin, verify_sha256, import_to_db as covenin_import
from data.importers.onsa import parse_onsa, import_to_db as onsa_import

REPO_ROOT = Path(__file__).parents[1]


@pytest.fixture
def db_path(tmp_path):
    db_file = tmp_path / 'test.db'
    conn = sqlite3.connect(str(db_file))
    migrations = REPO_ROOT / 'data' / 'migrations'
    conn.executescript((migrations / '001_init.sql').read_text())
    conn.executescript((migrations / '002_seed_staging.sql').read_text())
    conn.commit()
    conn.close()
    return str(db_file)


def test_covenin_importer(db_path):
    source_file = REPO_ROOT / 'data' / 'sources' / 'covenin-3661-2001.txt'
    verify_sha256(source_file)
    entries = parse_covenin(source_file)
    assert len(entries) >= 40
    covenin_import(db_path, entries, 'covenin-3661-2001')

    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT text, definition FROM seed_staging WHERE source='covenin-3661-2001'"
    ).fetchall()
    assert len(rows) >= 40
    for text, definition in rows:
        assert text and definition
        assert 'FONDONORMA' not in text

    # idempotency: re-run replaces, count unchanged
    covenin_import(db_path, entries, 'covenin-3661-2001')
    count2 = conn.execute(
        "SELECT COUNT(*) FROM seed_staging WHERE source='covenin-3661-2001'"
    ).fetchone()[0]
    assert count2 == len(rows)
    conn.close()


def test_onsa_importer(db_path):
    source_file = REPO_ROOT / 'data' / 'sources' / 'onsa-glosario.html'
    verify_sha256(source_file)
    entries = parse_onsa(source_file)
    assert len(entries) >= 15
    onsa_import(db_path, entries, 'onsa-glosario')

    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT text, definition FROM seed_staging WHERE source='onsa-glosario'"
    ).fetchall()
    assert len(rows) >= 15
    for text, definition in rows:
        assert text and definition
    conn.close()


def test_verify_sha256_rejects_unpinned_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("tampered content")
        temp_path = Path(f.name)
    try:
        with pytest.raises(ValueError, match="No SHA256 entry found"):
            verify_sha256(temp_path)
    finally:
        temp_path.unlink()


def test_verify_sha256_detects_tamper(tmp_path):
    """A pinned file whose bytes changed must be rejected (M12)."""
    import hashlib
    (tmp_path / 'data' / 'sources').mkdir(parents=True)
    target = tmp_path / 'data' / 'sources' / 'x.txt'
    target.write_text("original")
    good = hashlib.sha256(b"original").hexdigest()
    (tmp_path / 'data' / 'sources' / 'SHA256SUMS').write_text(
        f"{good}  data/sources/x.txt\n"
    )
    target.write_text("tampered")
    with pytest.raises(ValueError, match="Hash mismatch"):
        verify_sha256(target, repo_root=tmp_path)
