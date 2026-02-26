import dataclasses
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from vrt.config import Config
from vrt.server import app as flask_app
from vrt.session import Session


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _make_session(sid: str = "abc", status: str = "completed") -> Session:
    return Session(
        id=sid,
        title="test.m4a",
        created_at=datetime.now(timezone.utc).isoformat(),
        audio_filename="audio.m4a",
        target_lang="ko",
        status=status,
    )


# ── GET /api/sessions ──────────────────────────────────────────────────────


def test_list_sessions_empty(client):
    with patch("vrt.server.list_sessions", return_value=[]):
        resp = client.get("/api/sessions")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_list_sessions_returns_sessions(client):
    session = _make_session()
    with patch("vrt.server.list_sessions", return_value=[session]):
        resp = client.get("/api/sessions")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["id"] == "abc"


# ── GET /api/sessions/<id> ────────────────────────────────────────────────


def test_get_session_not_found(client):
    with patch("vrt.server.load_session", return_value=None):
        resp = client.get("/api/sessions/nonexistent")
    assert resp.status_code == 404


def test_get_session_found(client):
    session = _make_session()
    with patch("vrt.server.load_session", return_value=session):
        resp = client.get("/api/sessions/abc")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == "abc"


# ── POST /api/sessions ────────────────────────────────────────────────────


def test_post_session_creates_and_starts(client):
    session = _make_session(status="processing")
    mock_worker = MagicMock()
    with patch("vrt.server.create_session", return_value=session), \
         patch("vrt.server.start_processing", return_value=mock_worker), \
         patch("vrt.server.load_config", return_value=Config()):
        resp = client.post("/api/sessions", json={"file_path": "/tmp/test.m4a", "target_lang": "ko"})
    assert resp.status_code == 201
    assert resp.get_json()["id"] == "abc"


def test_post_session_missing_file_path(client):
    resp = client.post("/api/sessions", json={})
    assert resp.status_code == 400


# ── DELETE /api/sessions/<id> ─────────────────────────────────────────────


def test_delete_session(client):
    with patch("vrt.server.delete_session") as mock_del:
        resp = client.delete("/api/sessions/abc")
    assert resp.status_code == 204
    mock_del.assert_called_once_with("abc")


def test_delete_session_cancels_active_worker(client):
    session = _make_session(status="processing")
    mock_worker = MagicMock()
    with patch("vrt.server.create_session", return_value=session), \
         patch("vrt.server.start_processing", return_value=mock_worker), \
         patch("vrt.server.load_config", return_value=Config()):
        client.post("/api/sessions", json={"file_path": "/tmp/test.m4a"})

    with patch("vrt.server.delete_session"):
        client.delete("/api/sessions/abc")

    mock_worker.cancel.assert_called_once()


# ── PATCH /api/sessions/<id> ──────────────────────────────────────────────


def test_patch_session_title(client):
    session = _make_session()
    with patch("vrt.server.load_session", return_value=session), \
         patch("vrt.server.save_session") as mock_save:
        resp = client.patch("/api/sessions/abc", json={"title": "new title"})
    assert resp.status_code == 200
    assert resp.get_json()["title"] == "new title"
    mock_save.assert_called_once_with(session)


def test_patch_session_not_found(client):
    with patch("vrt.server.load_session", return_value=None):
        resp = client.patch("/api/sessions/nonexistent", json={"title": "x"})
    assert resp.status_code == 404


# ── GET /api/config ───────────────────────────────────────────────────────


def test_get_config(client):
    config = Config(openai_api_key="sk-test", soniox_api_key="soniox-test", target_lang="ko")
    with patch("vrt.server.load_config", return_value=config):
        resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["openai_api_key"] == "sk-test"
    assert data["target_lang"] == "ko"


# ── PATCH /api/config ─────────────────────────────────────────────────────


def test_patch_config_updates_key(client):
    config = Config()
    with patch("vrt.server.load_config", return_value=config), \
         patch("vrt.server.save_config") as mock_save:
        resp = client.patch("/api/config", json={"openai_api_key": "new-key"})
    assert resp.status_code == 200
    assert resp.get_json()["openai_api_key"] == "new-key"
    mock_save.assert_called_once()
