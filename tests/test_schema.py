import re
import sqlite3
import pytest
from pathlib import Path

FORBIDDEN_REGEX = re.compile(r'score|rating|rank|blacklist|global_id|real_name|precise_geo|device_id', re.IGNORECASE)

@pytest.fixture
def db_conn():
    migration_path = Path(__file__).parent.parent / 'data/migrations/001_init.sql'
    conn = sqlite3.connect(':memory:')
    conn.execute("PRAGMA foreign_keys = ON;")
    with open(migration_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    conn.executescript(sql_script)
    conn.commit()
    yield conn
    conn.close()

def test_apply_migration(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    expected_tables = {'terms', 'revisions', 'approvals', 'submission_tokens'}
    assert expected_tables.issubset(tables)

def test_schema_shield(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        for col in columns:
            col_name = col[1]
            assert not FORBIDDEN_REGEX.search(col_name), (
                f"Forbidden column/key name '{col_name}' detected in table '{table}'."
            )

def test_fts_smoke(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("""
        INSERT INTO terms (concept_id, lang, text, category, register, zone, example, audio_ref, source, status)
        VALUES ('concept-101', 'es', 'aplastamiento', 'medical', 'formal', 'universal', 'crush injury', 'audio.mp3', 'red-cross', 'published')
    """)
    db_conn.commit()

    cursor.execute("SELECT rowid, text, example FROM terms_fts WHERE terms_fts MATCH 'aplastamiento'")
    res = cursor.fetchall()
    assert len(res) == 1
    assert res[0][1] == 'aplastamiento'
    assert res[0][2] == 'crush injury'

def test_duplicate_approval_raises_integrity_error(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("""
        INSERT INTO approvals (target_type, target_id, reviewer_id, verdict, reason)
        VALUES ('term', 1, 99, 'approve', 'Looks perfect')
    """)
    db_conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO approvals (target_type, target_id, reviewer_id, verdict, reason)
            VALUES ('term', 1, 99, 'approve', 'Duplicate')
        """)
        db_conn.commit()

def test_term_with_history_cannot_be_deleted(db_conn):
    """M8: RESTRICT FK — deleting a term must not erase its revision history."""
    cursor = db_conn.cursor()
    cursor.execute("""
        INSERT INTO terms (concept_id, lang, text, category, register, source, status)
        VALUES ('concept-102', 'es', 'derrumbe', 'rescue', 'formal', 'covenin', 'published')
    """)
    term_id = cursor.lastrowid
    cursor.execute("""
        INSERT INTO revisions (term_id, proposed_fields, reason, status)
        VALUES (?, '{"text": "derrumbe estructural"}', 'more precise', 'pending_review')
    """, (term_id,))
    db_conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("DELETE FROM terms WHERE id = ?", (term_id,))
