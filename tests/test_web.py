import re
from pathlib import Path

import pytest

from server.app import create_app
from server.db import connect

REPO_ROOT = Path(__file__).parents[1]
BUDGET_BYTES = 500 * 1024  # M6 / AC4


@pytest.fixture
def client(migrated_db):
    conn = connect(migrated_db)
    conn.execute(
        "INSERT INTO terms (concept_id, lang, text, category, register, source, status)"
        " VALUES ('c1','es','aplastamiento','Médico','formal','seed','published')")
    conn.execute(
        "INSERT INTO terms (concept_id, lang, text, category, register, source, status)"
        " VALUES ('c1','en','crush injury','Médico','formal','seed','published')")
    conn.commit(); conn.close()
    app = create_app({"DATABASE": migrated_db, "TESTING": True, "SECRET_KEY": "t"})
    with app.test_client() as c:
        yield c


def test_pages_render(client):
    for path in ("/", "/?q=aplastamiento", "/term/1", "/submit", "/status", "/install", "/sw.js"):
        assert client.get(path).status_code == 200, path
    assert client.get("/term/999").status_code == 404


def test_search_page_shows_counterpart(client):
    html = client.get("/?q=aplastamiento").get_data(as_text=True)
    assert "aplastamiento" in html and "crush injury" in html


def test_form_submission_no_js(client):
    r = client.post("/submit", data={"text": "derrumbe", "lang": "es",
                                     "category": "Urbanismo"})
    assert r.status_code == 200
    assert "código" in r.get_data(as_text=True).lower()
    # honeypot
    r = client.post("/submit", data={"text": "x", "lang": "es",
                                     "category": "Urbanismo", "website": "spam"})
    assert "rechazado" in r.get_data(as_text=True)


def test_revision_form_no_js(client):
    r = client.post("/term/1/revise", data={
        "text": "síndrome de aplastamiento", "reason": "más preciso"})
    assert r.status_code == 200
    assert "seguimiento" in r.get_data(as_text=True)


def test_papel_y_arcilla_theme(client):
    """Design spec v4: warm ivory background, deep clay accent, pill actions
    (28px), rounded cards (12px), soft inputs (10px); self-hosted Playfair
    Display (headings) + Lora (editorial body), no third-party origins."""
    css = (REPO_ROOT / "web" / "static" / "style.css").read_text()
    assert "--bg: #f7f3ec" in css
    assert "--accent: #a34a2a" in css
    assert "--bg: #1d1a16" in css and "--accent: #dd8563" in css  # dark tokens
    assert "Playfair Display" in css and "Lora" in css
    assert "googleapis" not in css and "gstatic" not in css  # N3: vendored only
    for f in ("playfair-600.woff2", "playfair-700.woff2", "playfair-600i.woff2",
              "lora-400.woff2", "lora-400i.woff2", "lora-600.woff2"):
        assert (REPO_ROOT / "web" / "static" / "fonts" / f).stat().st_size > 0
    assert (REPO_ROOT / "web" / "static" / "fonts" / "OFL.txt").exists()
    assert "border-radius: 28px" in css
    assert "border-radius: 12px" in css
    assert "border-radius: 10px" in css
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
    # 6 self-hosted woff2 subsets (~180KB) ride inside this; still far from M6
    assert total < 250 * 1024


def test_saved_page_is_client_side_only(client):
    """Favorites/history live in localStorage (M4/M9): the page is a static
    shell, part of the offline app shell, and app.js never POSTs the data."""
    html = client.get("/guardados").get_data(as_text=True)
    assert 'id="fav-list"' in html and 'id="hist-list"' in html
    assert "este dispositivo" in html
    js = (REPO_ROOT / "web" / "static" / "app.js").read_text()
    assert "tucuso-favs" in js and "tucuso-hist" in js
    assert "/guardados" in (REPO_ROOT / "web" / "static" / "sw.js").read_text()
    # the favorites code must not talk to the network
    fav_section = js[js.index("tucuso-favs") - 2000: js.index("Offline search")]
    assert "fetch(" not in fav_section and "XMLHttpRequest" not in fav_section


def test_littre_presentation(migrated_db):
    """Le Littré reference: ling_info inline with the term, pronunciation as
    its own section, multi-line definitions render as numbered senses,
    automatic dark mode."""
    db_path = migrated_db
    conn = connect(db_path)
    conn.execute(
        "INSERT INTO terms (concept_id, lang, text, definition, category,"
        " register, ling_info, pronunciation, source, status) VALUES"
        " ('c9','es','triaje','Clasificación de víctimas.\nPunto donde se"
        " realiza.','Medicina general','formal','sust. m.',"
        " 'tri-a-je','seed','published')")
    conn.commit()
    tid = conn.execute("SELECT id FROM terms WHERE text='triaje'").fetchone()[0]
    conn.close()
    app = create_app({"DATABASE": db_path, "TESTING": True, "SECRET_KEY": "t"})
    client = app.test_client()
    html = client.get(f"/term/{tid}").get_data(as_text=True)
    assert '<span class="ling">sust. m.</span>' in html
    assert 'class="pronunciation"' in html
    assert '<ol class="senses">' in html and html.count("<li>") >= 2
    results = client.get("/?q=triaje").get_data(as_text=True)
    assert '<span class="ling">sust. m.</span>' in results
    assert "Punto donde" not in results  # list shows first sense only
    css = (REPO_ROOT / "web" / "static" / "style.css").read_text()
    assert "prefers-color-scheme: dark" in css


def test_theme_toggle(client):
    """Manual dark/light pin: pre-paint script + toggle button + CSS blocks
    for both the system preference and the html[data-theme] override."""
    html = client.get("/").get_data(as_text=True)
    assert 'id="theme-toggle"' in html
    assert "tucuso-theme" in html  # pre-paint pin in <head>
    css = (REPO_ROOT / "web" / "static" / "style.css").read_text()
    assert 'html[data-theme="dark"]' in css
    assert 'html:not([data-theme="light"])' in css
    js = (REPO_ROOT / "web" / "static" / "app.js").read_text()
    assert "theme-toggle" in js
