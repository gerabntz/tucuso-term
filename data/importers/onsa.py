import argparse
import html
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from data.importers.covenin import verify_sha256


def parse_onsa(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        raw = f.read()
    text = re.sub(r'<[^>]+>', '\n', raw)
    text = html.unescape(text)
    lines = [ln.strip() for ln in text.split('\n')]

    # isolate the glossary segment
    try:
        start = lines.index('Glosario de Emergencias y Desastres') + 1
    except ValueError:
        raise ValueError("Glossary heading not found in source")
    seg = [ln for ln in lines[start:] if ln and ln != '--']
    end = next((k for k, ln in enumerate(seg)
                if ln in ('Arriba', 'Responder') or ln.startswith('::')), len(seg))
    seg = seg[:end]

    def is_term(ln):
        return (ln == ln.upper() and len(ln) > 1
                and any(c.isalpha() for c in ln) and not ln.startswith('('))

    def is_section(ln):
        return len(ln) == 1 and ln.isalpha() and ln.isupper()

    entries = []
    current_section = None
    i = 0
    while i < len(seg):
        line = seg[i]
        if is_section(line):
            current_section = line
            i += 1
            continue
        if is_term(line) and current_section is not None:
            term = line
            body = []
            i += 1
            # optional abbreviation line like '(OAP):' folds into the term
            if i < len(seg) and re.match(r'^\([A-ZÁÉÍÓÚÑ]+\):?$', seg[i]):
                term = f"{term} {seg[i].rstrip(':')}"
                i += 1
            # definition fragments run until the next term/section
            while i < len(seg) and not is_term(seg[i]) and not is_section(seg[i]):
                body.append(seg[i])
                i += 1
            definition = re.sub(r'\s+', ' ', ' '.join(body)).strip()
            definition = re.sub(r'^\(([A-ZÁÉÍÓÚÑ]+)\):\s*', '', definition)
            definition = definition.lstrip(':').strip()
            if not definition:
                raise ValueError(f"Empty definition for term '{term}'")
            entries.append((current_section, term, definition))
            continue
        i += 1

    if len(entries) < 15:
        raise ValueError(f"Expected at least 15 entries, got {len(entries)}")
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
    parser = argparse.ArgumentParser(description='Import ONSA glossary into seed staging')
    parser.add_argument('db_path', help='Path to SQLite database')
    args = parser.parse_args()
    repo_root = Path(__file__).parents[2]
    source_file = repo_root / 'data' / 'sources' / 'onsa-glosario.html'
    verify_sha256(source_file)
    entries = parse_onsa(source_file)
    import_to_db(args.db_path, entries, 'onsa-glosario')
    print(f"Imported {len(entries)} entries from onsa-glosario")


if __name__ == '__main__':
    main()
