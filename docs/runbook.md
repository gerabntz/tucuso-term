# Runbook (T14; first deploy verified live 2026-07-03 — E3 done)

## First deploy (PythonAnywhere free tier, per ADR-001)

1. On PythonAnywhere, open a Bash console (Dashboard → Consoles → Bash).
   Clone and set up the venv (virtualenvwrapper ships preinstalled):
   ```bash
   git clone https://github.com/gerabntz/tucuso-term.git
   cd tucuso-term
   mkvirtualenv --python=/usr/bin/python3.12 tucuso-env
   pip install -r requirements.txt
   ```
   (If the repo is ever private: GitHub dropped password auth in 2021, so
   `git clone` will prompt for credentials — use a fine-grained PAT scoped to
   this repo as the password.)
2. Initialize the database once:
   ```bash
   python -c "from server.db import connect, apply_migrations; \
              c = connect('data/tucuso.db'); apply_migrations(c)"
   ```
3. Seed staging:
   ```bash
   python -m data.importers.unisdr         data/tucuso.db  # UNISDR 2009, free reuse w/ attribution
   python -m data.importers.original_vocab data/tucuso.db  # original definitions (machine-assisted draft)
   python -m data.importers.onsa           data/tucuso.db  # ONSA public glossary
   ```
   (COVENIN 3661 verbatim definitions are NOT seeded and its text is not in the
   repo — license-encumbered; replaced by the original-wording vocabulary above.
   `data/sources/covenin-3661-fingerprint.txt` keeps shingle hashes so CI can
   prove the original definitions copy no COVENIN wording.)
4. Publish the staged seeds (T13). Spot-check the list first, then bulk
   publish — rows with `en_equiv` become ES+EN concept pairs sharing a
   concept_id:
   ```bash
   python -m server.seed_publish data/tucuso.db --dry-run   # spot-check
   python -m server.seed_publish data/tucuso.db             # publish
   ```
   Idempotent: re-runs skip rows already published from the same source.
   Each term is recategorized on publish into the team's 5 domains
   (`data/importers/domains.py`). To wipe terms published under older
   categories and republish clean (bootstrap era only — refuses if any
   revision exists): `python -m server.seed_publish data/tucuso.db --reset`.
   On an existing database, apply any migration added after it was created
   (each file runs once, in order — e.g. 006, then 007):
   ```bash
   python -c "import sqlite3; \
              sqlite3.connect('data/tucuso.db').executescript( \
              open('data/migrations/007_ficha_fields.sql').read())"
   ```
5. Web app: **Add a new web app → Manual configuration** (not the "Flask"
   wizard — it scaffolds a template that doesn't match this repo) **→ Python
   3.12**. Virtualenv field: `tucuso-env` (PA expands it to the full
   `~/.virtualenvs/...` path). Source code / working directory:
   `/home/<user>/tucuso-term`.

   WSGI file (linked near the top of the Web tab) — replace the whole file
   with:
   ```python
   import sys, os

   project_home = '/home/<user>/tucuso-term'
   if project_home not in sys.path:
       sys.path.insert(0, project_home)

   os.environ['TUCUSO_DB'] = project_home + '/data/tucuso.db'
   os.environ['TUCUSO_SECRET'] = '<generate: python3 -c "import secrets; print(secrets.token_hex(32))">'

   from server.app import app as application
   ```
   Order matters: `server/app.py` runs `app = create_app()` at import time,
   which reads `os.environ` immediately — so the env vars must be set
   *before* the `from server.app import ...` line. There's no
   `python-dotenv` in requirements.txt (kept minimal on purpose), so this
   WSGI-file assignment is the env var mechanism, not a `.env` file.
6. Force HTTPS checkbox (bottom of the Web tab), then **Reload** (top of the
   Web tab — every WSGI/venv/code change needs this to take effect). Verify
   at `https://<user>.pythonanywhere.com/healthz` → `{"ok": true}`.

## Reviewers (invite-only, M10)

```bash
python -m server.reviewer_cli invite ana  data/tucuso.db
python -m server.reviewer_cli link   ana  data/tucuso.db   # send out-of-band
python -m server.reviewer_cli disable ana data/tucuso.db
```

Links are single-use and expire in 15 minutes; issue a fresh one per session.

## Routine operations

- **Backup** = copy `data/tucuso.db` (SQLite single file). The public export
  (`/api/export/terms.json|csv`) is the community's own escape hatch (M7).
- **Token hygiene**: expired submission tokens purge themselves on lookup;
  to force it: `python -c "..."` calling `server.tokens.purge_expired`.
- **Never** edit published rows in SQL by hand (M8) — use a revision through
  the queue, even for typos.

## Incident notes

- Site down ≠ data loss: readers keep the offline snapshot (M5/M11).
- If a bad term got published: veto cannot un-publish; submit a correcting
  revision and fast-track it through two reviewers. History stays visible
  by design.
