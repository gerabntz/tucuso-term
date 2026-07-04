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
"""
import argparse
import uuid

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
            if dry_run:
                print(f"would publish [{row['source']}] {row['text']}"
                      + (f" ⇄ {row['en_equiv']}" if row["en_equiv"] else ""))
                continue
            concept_id = uuid.uuid4().hex
            conn.execute(
                "INSERT INTO terms (concept_id, lang, text, definition,"
                " category, register, example, source, status)"
                " VALUES (?,?,?,?,?,?,?,?, 'published')",
                (concept_id, row["lang"], row["text"], row["definition"],
                 row["category"], row["register"], row["example"],
                 row["source"]))
            if row["en_equiv"]:
                conn.execute(
                    "INSERT INTO terms (concept_id, lang, text, definition,"
                    " category, register, example, source, status)"
                    " VALUES (?, 'en', ?, NULL, ?, ?, NULL, ?, 'published')",
                    (concept_id, row["en_equiv"], row["category"],
                     row["register"], row["source"]))
    return published, skipped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("db_path")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    conn = connect(args.db_path)
    published, skipped = publish_seeds(conn, dry_run=args.dry_run)
    verb = "would publish" if args.dry_run else "published"
    print(f"{verb} {published} staging rows ({skipped} already live)")
    conn.close()


if __name__ == "__main__":
    main()
