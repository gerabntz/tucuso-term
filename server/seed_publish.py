"""T13 — bulk-publish spot-checked seed rows into `terms`.

Seeds are the one sanctioned bypass of the 2-reviewer quorum: their sources
were already validated (pinned, licensed, fingerprint-checked in CI), and the
operator running this command IS the human gate. Community submissions never
pass through here.

Rows with an `en_equiv` publish as concept PAIRS: an ES row plus an EN row
sharing a fresh concept_id. Idempotent: a staging row whose (source, text)
already exists among published terms is skipped, so re-runs add nothing.

    python -m server.seed_publish data/tucuso.db            # publish
    python -m server.seed_publish data/tucuso.db --dry-run  # list only
    python -m server.seed_publish data/tucuso.db --reset    # wipe + republish

Categories: staging rows carry the pre-2026-07 defaults, so each term is
recategorized on publish via data/importers/domains.py (the team's 5 domains).

--reset deletes ALL terms and republishes the seeds — an operator-only bootstrap
action for the pre-launch era. It refuses to run if any revision exists (M8:
once real history accumulates, corrections must travel through the queue).
"""
import argparse
import sqlite3
import sys
import uuid

from data.importers.domains import DOMAIN_MAP, DEFAULT_DOMAIN
from server.db import connect


def publish_seeds(conn, dry_run=False):
    """Returns (published_count, skipped_count). Counts staging rows."""
    published = skipped = 0
    rows = conn.execute(
        "SELECT * FROM seed_staging ORDER BY source, id").fetchall()
    with conn:
        for row in rows:
            exists = conn.execute(
                "SELECT 1 FROM terms WHERE source=? AND text=? AND lang=?"
                " AND status='published'",
                (row["source"], row["text"], row["lang"])).fetchone()
            if exists:
                skipped += 1
                continue
            published += 1
            category = DOMAIN_MAP.get(row["text"], DEFAULT_DOMAIN)
            if dry_run:
                print(f"would publish [{row['source']}] {row['text']}"
                      + (f" ⇄ {row['en_equiv']}" if row["en_equiv"] else "")
                      + f" [{category}]")
                continue
            concept_id = uuid.uuid4().hex
            conn.execute(
                "INSERT INTO terms (concept_id, lang, text, definition,"
                " category, register, example, source, status)"
                " VALUES (?,?,?,?,?,?,?,?, 'published')",
                (concept_id, row["lang"], row["text"], row["definition"],
                 category, row["register"], row["example"],
                 row["source"]))
            if row["en_equiv"]:
                conn.execute(
                    "INSERT INTO terms (concept_id, lang, text, definition,"
                    " category, register, example, source, status)"
                    " VALUES (?, 'en', ?, NULL, ?, ?, NULL, ?, 'published')",
                    (concept_id, row["en_equiv"], category,
                     row["register"], row["source"]))
    return published, skipped


def reset_terms(conn):
    """Delete every term so the seeds republish clean. Bootstrap-era only."""
    revisions = conn.execute("SELECT COUNT(*) FROM revisions").fetchone()[0]
    if revisions:
        raise sqlite3.IntegrityError(
            f"{revisions} revision(s) exist — history is immutable (M8);"
            " reset is only for the pre-launch bootstrap era")
    with conn:
        n = conn.execute("DELETE FROM terms").rowcount
    print(f"deleted {n} terms")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("db_path")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reset", action="store_true",
                        help="delete ALL terms first, then republish seeds")
    args = parser.parse_args()
    conn = connect(args.db_path)
    if args.reset and not args.dry_run:
        try:
            reset_terms(conn)
        except sqlite3.IntegrityError as exc:
            sys.exit(f"reset refused: {exc}")
    published, skipped = publish_seeds(conn, dry_run=args.dry_run)
    verb = "would publish" if args.dry_run else "published"
    print(f"{verb} {published} staging rows ({skipped} already live)")
    conn.close()


if __name__ == "__main__":
    main()
