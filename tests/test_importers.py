import sqlite3
import tempfile
from pathlib import Path

import pytest

from data.importers.common import verify_sha256, import_rows
from data.importers.onsa import parse_onsa, to_rows, SOURCE as ONSA_SOURCE

REPO_ROOT = Path(__file__).parents[1]


@pytest.fixture
def db_path(migrated_db):
    return migrated_db


def test_onsa_importer(db_path):
    source_file = REPO_ROOT / 'data' / 'sources' / 'onsa-glosario.html'
    verify_sha256(source_file)
    entries = parse_onsa(source_file)
    assert len(entries) >= 15
    import_rows(db_path, to_rows(entries), ONSA_SOURCE)

    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT text, definition FROM seed_staging WHERE source=?",
        (ONSA_SOURCE,)).fetchall()
    assert len(rows) >= 15
    for text, definition in rows:
        assert text and definition

    # idempotency: re-run replaces, count unchanged
    import_rows(db_path, to_rows(entries), ONSA_SOURCE)
    count2 = conn.execute(
        "SELECT COUNT(*) FROM seed_staging WHERE source=?",
        (ONSA_SOURCE,)).fetchone()[0]
    assert count2 == len(rows)
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
