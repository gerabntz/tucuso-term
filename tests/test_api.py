import pytest

from server.app import create_app
from server.db import connect


@pytest.fixture
def client(migrated_db):
    app = create_app({"DATABASE": migrated_db, "TESTING": True, "SECRET_KEY": "t"})
    with app.test_client() as c:
        yield c


def submit(client, **over):
    payload = dict(text="colapso estructural", lang="es", category="Urbanismo")
    payload.update(over)
    return client.post("/api/terms", json=payload)


def test_submit_returns_token_and_pending(client):
    r = submit(client)
    assert r.status_code == 201
    assert r.json["status"] == "pending_review"
    tok = r.json["token"]
    s = client.get(f"/api/status/{tok}")
    assert s.status_code == 200 and s.json["status"] == "pending_review"


def test_honeypot_and_validation(client):
    assert submit(client, website="http://spam").status_code == 400
    assert submit(client, category="Nope").status_code == 400
    assert submit(client, lang="xx").status_code == 400
    r = client.post("/api/terms", json={"lang": "es"})
    assert r.status_code == 400


def test_pending_terms_are_not_readable(client):
    submit(client)
    assert client.get("/api/terms/1").status_code == 404  # unpublished = invisible


def test_no_update_or_delete_routes(client):
    """N5/M8: the API must not expose in-place mutation of terms."""
    assert client.put("/api/terms/1", json={}).status_code == 405
    assert client.patch("/api/terms/1", json={}).status_code == 405
    assert client.delete("/api/terms/1").status_code == 405


def test_public_timestamps_are_coarsened(client, tmp_path):
    submit(client)
    conn = connect(str(tmp_path / "t.db"))
    conn.execute("UPDATE terms SET status='published' WHERE id=1")
    conn.commit(); conn.close()
    r = client.get("/api/terms/1")
    assert r.status_code == 200
    assert len(r.json["date"]) == 10           # YYYY-MM-DD only (M9)
    assert "created_at" not in r.json


def test_correction_requires_published_base_and_reason(client, tmp_path):
    submit(client)
    r = client.post("/api/terms/1/revisions",
                    json={"proposed_fields": {"text": "x"}, "reason": "y"})
    assert r.status_code == 404                 # base not published yet
    conn = connect(str(tmp_path / "t.db"))
    conn.execute("UPDATE terms SET status='published' WHERE id=1")
    conn.commit(); conn.close()
    assert client.post("/api/terms/1/revisions",
                       json={"proposed_fields": {"text": "x"}}).status_code == 400
    r = client.post("/api/terms/1/revisions",
                    json={"proposed_fields": {"text": "colapso parcial"},
                          "reason": "más preciso"})
    assert r.status_code == 201 and r.json["token"]


def test_rate_limit_returns_429(client):
    from server.ratelimit import MAX_PER_WINDOW
    for i in range(MAX_PER_WINDOW):
        assert submit(client, text=f"término {i}").status_code == 201
    assert submit(client, text="one too many").status_code == 429
