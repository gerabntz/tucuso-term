"""Immutable policy tests (bundle: constraints.md M3/M4/N3, evals AC2/AC4).

These tests are CI law: they must never be deleted, skipped, or xfail'd.
An agent proposing to weaken them must stop and escalate (E4).
"""
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# M3/N3 — no LLM, analytics, or tracking SDK may enter the runtime.
FORBIDDEN_DEPS = re.compile(
    r"^(openai|anthropic|google-generativeai|litellm|langchain|transformers"
    r"|sentry|segment|mixpanel|amplitude|posthog|google-analytics)",
    re.I,
)

# M4 — anti-surveillance schema shield (C2C FORBIDDEN_KEYS pattern).
FORBIDDEN_KEYS = re.compile(
    r"score|rating|rank|blacklist|global_id|real_name|precise_geo|device_id", re.I
)


def test_lockfile_has_no_forbidden_sdks():
    for line in (ROOT / "requirements.txt").read_text().splitlines():
        pkg = line.split("#")[0].strip()
        assert not (pkg and FORBIDDEN_DEPS.match(pkg)), f"forbidden dependency: {pkg}"


def test_fts5_available():
    con = sqlite3.connect(":memory:")
    con.execute("CREATE VIRTUAL TABLE t USING fts5(x)")  # raises if FTS5 missing


def test_schema_shield():
    """Every column in every migration/live schema must pass the shield.

    T2 extends this to run against the real migrations; until then it guards
    any .sql files that appear under data/.
    """
    for sql_file in (ROOT / "data").rglob("*.sql"):
        for m in re.finditer(r"^\s*(\w+)\s+\w+", sql_file.read_text(), re.M):
            col = m.group(1)
            assert not FORBIDDEN_KEYS.search(col), (
                f"surveillance-capable column '{col}' in {sql_file.name} (M4)"
            )
