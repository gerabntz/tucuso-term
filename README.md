# Tucuso-term

Community EN<>ES crisis-interpreting glossary for the Venezuela earthquake
response. Offline-readable PWA where volunteer interpreters search validated
terminology, submit new terms, and propose corrections — every publication
gated by a 2-human bilingual reviewer quorum.

- **No accounts for readers or submitters.** Reviewers are the only accounts.
- **No runtime LLM.** Humans decide correctness.
- **Anti-surveillance schema.** No field can profile a person.
- **Offline after first load**, ≤500 KB app shell, warm terracotta theme built
  for daylight outdoor use.
- **Open export:** versioned SQLite/CSV/JSON — the future mobile app's content pipeline.

## Layout

| Dir | Contents |
|---|---|
| `data/` | SQLite schema/migrations, seed importers (UNISDR 2009, ONSA, original vocabulary), vendored sources |
| `server/` | Flask app: search API, submissions, revisions, moderation quorum |
| `web/` | Jinja2 templates, stylesheet, vanilla-JS service worker |
| `tests/` | pytest suite incl. constraint policy tests (schema shield, budget, lockfile) |
| `docs/` | ADRs, runbook. Spec bundle lives at `../workflows/tucuso-term-website/` |

## Dev quickstart

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest
flask --app server.app run
```

Stack rationale: `docs/adr-001-stack.md`.

## License

- **Code**: [GPL-3.0-or-later](LICENSE) — share-alike; derivatives must stay open.
- **Glossary content & seed data**: [CC BY-SA 4.0](data/LICENSE-DATA) — reuse
  freely with attribution, share alike. Vendored third-party sources keep their
  own terms: UNISDR 2009 terminology permits free reuse with attribution; the
  ONSA public glossary is included as-published for provenance.
