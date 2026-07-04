from datetime import datetime, timedelta, timezone

import pytest

from server.app import create_app
from server.auth import invite_reviewer, issue_magic_link
from server.db import connect


@pytest.fixture
def env(migrated_db):
    db_path = migrated_db
    conn = connect(db_path)
    invite_reviewer(conn, "ana")
    invite_reviewer(conn, "beto")
    conn.execute(
        "INSERT INTO terms (concept_id, lang, text, category, register, source, status)"
        " VALUES ('c1','es','derrumbe','Construcción/Rescate','formal','community','pending_review')")
    conn.commit()
    app = create_app({"DATABASE": db_path, "TESTING": True, "SECRET_KEY": "t"})
    yield app, conn
    conn.close()


def login(app, conn, handle):
    client = app.test_client()
    token = issue_magic_link(conn, handle)
    assert client.get(f"/mod/login/{token}").status_code == 302
    return client


def test_queue_requires_auth(env):
    app, _ = env
    assert app.test_client().get("/mod/queue").status_code == 401
    assert app.test_client().post("/mod/vote", data={}).status_code == 401


def test_magic_link_is_single_use_and_expirable(env):
    app, conn = env
    token = issue_magic_link(conn, "ana")
    c = app.test_client()
    assert c.get(f"/mod/login/{token}").status_code == 302
    assert app.test_client().get(f"/mod/login/{token}").status_code == 403  # burned (C10)

    expired = issue_magic_link(conn, "ana")
    conn.execute("UPDATE magic_links SET expires_at=? WHERE token=?",
                 ((datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(), expired))
    conn.commit()
    assert app.test_client().get(f"/mod/login/{expired}").status_code == 403


def test_disabled_reviewer_cannot_login(env):
    app, conn = env
    token = issue_magic_link(conn, "ana")
    conn.execute("UPDATE reviewers SET active=0 WHERE handle='ana'")
    conn.commit()
    assert app.test_client().get(f"/mod/login/{token}").status_code == 403


def test_quorum_e2e_two_reviewers_publish(env):
    app, conn = env
    ana = login(app, conn, "ana")
    assert "derrumbe" in ana.get("/mod/queue").get_data(as_text=True)

    ana.post("/mod/vote", data={"target_type": "term", "target_id": 1,
                                "verdict": "approve"})
    # same reviewer cannot double-approve (C1)
    r = ana.post("/mod/vote", data={"target_type": "term", "target_id": 1,
                                    "verdict": "approve"}, follow_redirects=True)
    assert "Ya votó" in r.get_data(as_text=True)
    assert conn.execute("SELECT status FROM terms WHERE id=1").fetchone()[0] == "pending_review"

    beto = login(app, conn, "beto")
    beto.post("/mod/vote", data={"target_type": "term", "target_id": 1,
                                 "verdict": "approve"})
    assert conn.execute("SELECT status FROM terms WHERE id=1").fetchone()[0] == "published"


def test_veto_needs_reason_and_rejects(env):
    app, conn = env
    ana = login(app, conn, "ana")
    r = ana.post("/mod/vote", data={"target_type": "term", "target_id": 1,
                                    "verdict": "veto"}, follow_redirects=True)
    assert "rechazado" in r.get_data(as_text=True)
    ana.post("/mod/vote", data={"target_type": "term", "target_id": 1,
                                "verdict": "veto", "reason": "traducción errónea"})
    assert conn.execute("SELECT status FROM terms WHERE id=1").fetchone()[0] == "rejected"
