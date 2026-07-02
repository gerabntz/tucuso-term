import argparse
import hashlib
import re
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


def parse_covenin(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    entries = []
    in_definitions = False
    current_term = None
    current_ref = None
    current_def = []

    def flush():
        if current_term is not None:
            definition = ' '.join(current_def).strip()
            if not definition:
                raise ValueError(f"Empty definition for term '{current_term}'")
            entries.append((current_ref, current_term, definition))

    for line in lines:
        if 'FONDONORMA - PARA USO EXCLUSIVO' in line:
            continue
        stripped = line.strip()
        if stripped.isdigit():
            continue
        if not in_definitions:
            if re.match(r'^3\s+DEFINICIONES$', stripped):
                in_definitions = True
            continue
        if re.match(r'^4\s+\S', stripped):
            break
        heading_match = re.match(r'^(3\.\d+)\s+(.+)$', stripped)
        if heading_match:
            flush()
            current_ref = heading_match.group(1)
            current_term = heading_match.group(2).strip()
            current_def = []
        elif current_term is not None and stripped:
            current_def.append(stripped)
    flush()

    if len(entries) < 40:
        raise ValueError(f"Expected at least 40 entries, got {len(entries)}")
    return entries


def import_to_db(db_path, entries, source):
    conn = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        with conn:
            conn.execute("DELETE FROM seed_staging WHERE source=?", (source,))
            conn.executemany(
                "INSERT INTO seed_staging (source, source_ref, lang, text, definition,"
                " category, register, imported_at) VALUES (?, ?, 'es', ?, ?,"
                " 'Protocolos', 'formal', ?)",
                [(source, ref, text, definition, now) for ref, text, definition in entries],
            )
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='Import COVENIN 3661-2001 into seed staging')
    parser.add_argument('db_path', help='Path to SQLite database')
    args = parser.parse_args()
    repo_root = Path(__file__).parents[2]
    source_file = repo_root / 'data' / 'sources' / 'covenin-3661-2001.txt'
    verify_sha256(source_file)
    entries = parse_covenin(source_file)
    import_to_db(args.db_path, entries, 'covenin-3661-2001')
    print(f"Imported {len(entries)} entries from covenin-3661-2001")


if __name__ == '__main__':
    main()
