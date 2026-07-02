import re
from pathlib import Path

import pytest

from server.app import create_app
from server.db import apply_migrations, connect

REPO_ROOT = Path(__file__).parents[1]
BUDGET_BYTES = 500 * 1024  # M6 / AC4


@pytest.fixture
def client(tmp_path):
    db_path = str(tmp_path / "t.db")
    conn = connect(db_path)
    apply_migrations(conn)
    conn.execute(
        "INSERT INTO terms (concept_id, lang, text, category, register, source, status)"
        " VALUES ('c1','es','aplastamiento','Médico','formal','seed','published')")
    conn.execute(
        "INSERT INTO terms (concept_id, lang, text, category, register, source, status)"
        " VALUES ('c1','en','crush injury','Médico','formal','seed','published')")
    conn.commit(); conn.close()
    app = create_app({"DATABASE": db_path, "TESTING": True, "SECRET_KEY": "t"})
    with app.test_client() as c:
        yield c


def test_pages_render(client):
    for path in ("/", "/?q=aplastamiento", "/term/1", "/submit", "/status", "/sw.js"):
        assert client.get(path).status_code == 200, path
    assert client.get("/term/999").status_code == 404


def test_search_page_shows_counterpart(client):
    html = client.get("/?q=aplastamiento").get_data(as_text=True)
    assert "aplastamiento" in html and "crush injury" in html


def test_form_submission_no_js(client):
    r = client.post("/submit", data={"text": "derrumbe", "lang": "es",
                                     "category": "Construcción/Rescate"})
    assert r.status_code == 200
    assert "código" in r.get_data(as_text=True).lower()
    # honeypot
    r = client.post("/submit", data={"text": "x", "lang": "es",
                                     "category": "Médico", "website": "spam"})
    assert "rechazado" in r.get_data(as_text=True)


def test_revision_form_no_js(client):
    r = client.post("/term/1/revise", data={
        "text": "síndrome de aplastamiento", "reason": "más preciso"})
    assert r.status_code == 200
    assert "seguimiento" in r.get_data(as_text=True)


def test_dark_mode_default(client):
    css = (REPO_ROOT / "web" / "static" / "style.css").read_text()
    assert "--bg: #111418" in css
    html = client.get("/").get_data(as_text=True)
    assert 'lang="es"' in html  # ES-first UI


def test_no_third_party_origins(client):
    """N3/AC4: the app shell must reference no external hosts."""
    pages = [client.get(p).get_data(as_text=True)
             for p in ("/", "/submit", "/status")]
    pages.append((REPO_ROOT / "web" / "static" / "app.js").read_text())
    pages.append((REPO_ROOT / "web" / "static" / "sw.js").read_text())
    for content in pages:
        for url in re.findall(r'https?://[^\s"\'<>)]+', content):
            assert False, f"external origin referenced: {url}"


def test_first_load_budget(client):
    """M6: shell page + all local assets it references must fit 500 KB."""
    total = len(client.get("/").get_data())
    for asset in ("/static/style.css", "/static/app.js", "/static/manifest.json",
                  "/static/icon.svg", "/sw.js"):
        total += len(client.get(asset).get_data())
    assert total < BUDGET_BYTES, f"first load is {total} bytes"
    assert total < 50 * 1024  # we should be nowhere near the cap
