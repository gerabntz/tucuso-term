"""Shared importer plumbing: SHA-256 source pinning (M12) and the staging writer."""
import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def verify_sha256(path, repo_root=None):
    if repo_root is None:
        repo_root = Path(__file__).parents[2]
    sums_path = repo_root / 'data' / 'sources' / 'SHA256SUMS'
    if not sums_path.exists():
        raise ValueError(f"SHA256SUMS not found at {sums_path}")
    try:
        rel_path = Path(path).resolve().relative_to(repo_root.resolve())
    except ValueError:
        raise ValueError(f"No SHA256 entry found for {path} (outside repo)")
    with open(sums_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('  ')
            if len(parts) < 2:
                continue
            hex_hash, file_rel = parts[0], parts[-1]
            if file_rel == str(rel_path):
                with open(path, 'rb') as ff:
                    actual_hash = hashlib.sha256(ff.read()).hexdigest()
                if actual_hash != hex_hash:
                    raise ValueError(
                        f"Hash mismatch for {path}: expected {hex_hash}, got {actual_hash}"
                    )
                return
    raise ValueError(f"No SHA256 entry found for {rel_path} in SHA256SUMS")


def import_rows(db_path, rows, source):
    """Staging writer: rows are dicts with source_ref, text, definition,
    and optional en_equiv / example. Single transaction, idempotent per source."""
    conn = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        with conn:
            conn.execute("DELETE FROM seed_staging WHERE source=?", (source,))
            conn.executemany(
                "INSERT INTO seed_staging (source, source_ref, lang, text,"
                " definition, en_equiv, example, category, register, imported_at)"
                # staging keeps the legacy default category; seed_publish
                # recategorizes into the current domains on publish
                " VALUES (?, ?, 'es', ?, ?, ?, ?, 'Protocolos', 'formal', ?)",
                [(source, r.get("source_ref"), r["text"], r["definition"],
                  r.get("en_equiv"), r.get("example"), now) for r in rows],
            )
    finally:
        conn.close()
