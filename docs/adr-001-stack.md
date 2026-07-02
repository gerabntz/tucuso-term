# ADR-001: Stack and hosting

**Status:** Accepted (hosting pick pending Angelus confirmation)
**Date:** 2026-07-02
**Task:** T1 (workflows/tucuso-term-website/tasks.md)

## Context

Tucuso-term is an EN<>ES crisis-interpreting glossary for the Venezuela earthquake
response: offline-readable PWA, ≤500 KB first load (M6), zero runtime LLM (M3),
zero third-party runtime origins (N3), SQLite+FTS5 as source of truth, 2-human
quorum moderation, anti-surveillance schema (M4). Traffic is small (hundreds of
users). Spec mandates static-first + tiny API, boring tech, free-tier hosting.
Reusable patterns (quorum `resolve()`, FORBIDDEN_KEYS shield, transient tokens)
come from the C2C repo, which is Python.

## Decision

| Layer | Choice | Because |
|---|---|---|
| Language | Python 3.12 | C2C patterns port directly; Angelus's ecosystem; boring |
| Web framework | Flask 3 (WSGI) | Lowest-rung boring tech; WSGI is what the free host runs natively; no async needed at this traffic |
| Database | stdlib `sqlite3` + FTS5 | Investigation-doc recommendation; single file = trivial backup/export; no ORM (N5/M8 immutability is easier to enforce with explicit SQL) |
| Templates | Jinja2, server-rendered | No SPA framework → M6 budget is easy; works on 2 GB-RAM Android browsers |
| Front-end JS | Vanilla, hand-rolled service worker | No third-party runtime deps (N3); PWA offline read + client-side snapshot search (M5/M11) |
| CSS | Single hand-written stylesheet, dark default | Budget + PRD pillar |
| Hosting (recommended) | PythonAnywhere free tier | Genuinely $0, persistent disk for SQLite, WSGI-native, HTTPS included. Fallback: any small VPS (~€3/mo) or Fly.io machine — same code, gunicorn |
| CI | GitHub Actions: pytest + constraint checks | AC2 shield test, M6 budget check, M3 lockfile check run as immutable policy tests |

## Rejected alternatives

- **FastAPI/ASGI** — better tech, wrong rung: free WSGI hosting is more available, and nothing here needs async.
- **Node/Hono** — would orphan the C2C Python patterns.
- **Static-site-only (no server)** — can't do submissions/moderation; the API is the point of the curation surface.
- **Postgres / hosted DB** — a second service to pay for and back up; SQLite is the deliverable format anyway (I5/M7).

## Repo state note

`github.com/gerabntz/tucuso-term` returned **404 unauthenticated** on 2026-07-02
(private or not yet created). This scaffold was created locally at
`~/Documents/MEGA/IA/Tucuso-term/tucuso-term/`; Angelus performs the first push
after verifying the remote (open gate in .specsmith.json).

## Consequences

- All executor nodes (T2+) target Python 3.12 / Flask / sqlite3; `requirements.txt` is the M3 lockfile surface (CI fails if any LLM/analytics SDK appears).
- Deployment = copy repo + `flask db-init` + point WSGI at `server/app.py` (runbook at T14).
- FTS5 availability must be asserted at startup (some minimal builds omit it) — encoded as a T2 test.
