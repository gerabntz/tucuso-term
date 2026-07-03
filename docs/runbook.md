# Runbook (draft — T14; Angelus executes the deploy, E3)

## First deploy (PythonAnywhere free tier, per ADR-001)

1. Push this repo to GitHub, then on PythonAnywhere: clone it, create a
   virtualenv (3.12), `pip install -r requirements.txt`.
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
   (`data/importers/covenin.py` is retained for its parsing machinery but its
   verbatim COVENIN definitions are NOT seeded — license-encumbered; replaced
   by the original-wording vocabulary above.)
   Publishing staged seeds is T13: human spot-check, then bulk publish. The
   original-draft + UNISDR rows include `en_equiv`, so T13 publishes ES+EN
   concept pairs.
4. Web app config: WSGI file points at `server.app:app`. Set env vars
   `TUCUSO_DB=/home/<user>/tucuso-term/data/tucuso.db` and a strong
   `TUCUSO_SECRET` (rotating it invalidates reviewer sessions — fine).
5. Force HTTPS in the PythonAnywhere web tab.

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
