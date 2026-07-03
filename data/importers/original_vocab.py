"""Importer for the Tucuso original-vocabulary draft (T3 replacement).

The term inventory is standard Venezuelan risk-management vocabulary; the
definitions and examples are ORIGINAL wording written for this project
(machine-assisted draft), replacing the license-encumbered COVENIN text.
Source label keeps that visible all the way to the review queue.
"""
import argparse
import json
from pathlib import Path

from data.importers.common import verify_sha256, import_rows

SOURCE = "tucuso-original-draft"
MIN_ENTRIES = 40


def parse_vocab(filepath):
    data = json.loads(Path(filepath).read_text(encoding="utf-8"))
    rows = []
    for t in data["terms"]:
        if not t.get("es") or not t.get("def") or not t.get("en"):
            raise ValueError(f"incomplete entry: {t!r}")
        rows.append(dict(source_ref=None, text=t["es"], definition=t["def"],
                         en_equiv=t["en"], example=t.get("ex")))
    if len(rows) < MIN_ENTRIES:
        raise ValueError(f"Expected at least {MIN_ENTRIES} entries, got {len(rows)}")
    return rows


def main():
    parser = argparse.ArgumentParser(description="Import Tucuso original vocabulary draft")
    parser.add_argument("db_path")
    args = parser.parse_args()
    repo_root = Path(__file__).parents[2]
    source_file = repo_root / "data" / "sources" / "vocabulario-ve-original.json"
    verify_sha256(source_file)
    rows = parse_vocab(source_file)
    import_rows(args.db_path, rows, SOURCE)
    print(f"Imported {len(rows)} entries from {SOURCE}")


if __name__ == "__main__":
    main()
