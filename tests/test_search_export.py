import csv
import io

import pytest

from server.app import create_app
from server.db import connect


@pytest.fixture
def client(migrated_db):
    conn = connect(migrated_db)
    rows = [
        ("c1", "es", "aplastamiento", "Médico", "síndrome de aplastamiento tras derrumbe", "published"),
        ("c1", "en", "crush injury", "Médico", None, "published"),
        ("c2", "es", "secreto", "Médico", None, "pending_review"),
    ]
    for concept, lang, text, cat, example, status in rows:
        conn.execute(
            "INSERT INTO terms (concept_id, lang, text, category, register,"
            " example, source, status) VALUES (?, ?, ?, ?, 'formal', ?, 'seed', ?)",
            (concept, lang, text, cat, example, status))
    conn.commit()
    conn.close()
    app = create_app({"DATABASE": migrated_db, "TESTING": True, "SECRET_KEY": "t"})
    with app.test_client() as c:
        yield c


def test_search_hit_with_counterpart(client):
    r = client.get("/api/search?q=aplastamiento")
    assert r.status_code == 200
    assert len(r.json["results"]) == 1
    hit = r.json["results"][0]
    assert hit["text"] == "aplastamiento"
    assert hit["counterparts"][0]["text"] == "crush injury"


def test_search_is_accent_insensitive(client):
    for q in ("sindrome", "síndrome"):
        r = client.get(f"/api/search?q={q}")
        assert r.status_code == 200
        assert len(r.json["results"]) == 1, q


def test_search_prefix_and_reverse_direction(client):
    r = client.get("/api/search?q=crush")
    assert len(r.json["results"]) == 1
    assert r.json["results"][0]["lang"] == "en"
    assert r.json["results"][0]["counterparts"][0]["lang"] == "es"


def test_search_filters(client):
    assert len(client.get("/api/search?q=aplastamiento&lang=es").json["results"]) == 1
    assert len(client.get("/api/search?q=aplastamiento&lang=en").json["results"]) == 0
    assert len(client.get("/api/search?q=aplastamiento&category=Clima").json["results"]) == 0


def test_pending_terms_never_surface(client):
    assert client.get("/api/search?q=secreto").json["results"] == []


def test_malicious_or_empty_query_rejected(client):
    assert client.get('/api/search?q="*)(').status_code == 400
    assert client.get("/api/search?q=").status_code == 400
    assert client.get("/api/search?q=" + "x" * 101).status_code == 400


def test_export_json(client):
    r = client.get("/api/export/terms.json")
    assert r.status_code == 200
    assert r.json["version"] > 0
    texts = {t["text"] for t in r.json["terms"]}
    assert texts == {"aplastamiento", "crush injury"}   # pending excluded
    assert r.headers["ETag"] == str(r.json["version"])
    assert "max-age" in r.headers["Cache-Control"]


def test_export_csv(client):
    r = client.get("/api/export/terms.csv")
    assert r.status_code == 200
    rows = list(csv.DictReader(io.StringIO(r.get_data(as_text=True))))
    assert len(rows) == 2
    assert {row["text"] for row in rows} == {"aplastamiento", "crush injury"}
    assert r.headers.get("ETag")
