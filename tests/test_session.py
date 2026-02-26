import time
from pathlib import Path

import pytest

from vrt.session import (
    Session,
    create_session,
    delete_session,
    list_sessions,
    load_session,
    save_session,
)


@pytest.fixture(autouse=True)
def patch_sessions_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("vrt.session.SESSIONS_DIR", tmp_path)


def _make_audio(tmp_path: Path, name: str = "test.m4a") -> str:
    f = tmp_path / name
    f.write_bytes(b"fake-audio")
    return str(f)


def test_create_session_copies_audio(tmp_path):
    audio = _make_audio(tmp_path)
    session = create_session("test.m4a", audio, "ko")

    session_dir = tmp_path / session.id
    assert (session_dir / session.audio_filename).exists()


def test_create_session_initial_status_is_processing(tmp_path):
    audio = _make_audio(tmp_path)
    session = create_session("test.m4a", audio, "ko")
    assert session.status == "processing"


def test_save_and_load_session(tmp_path):
    audio = _make_audio(tmp_path)
    session = create_session("test.m4a", audio, "ko")

    session.status = "completed"
    session.speaker_names = {"1": "화자 1", "2": "화자 2"}
    session.segments = [{"start": 0.0, "end": 1.5, "speaker": "1", "original": "xin chào", "translated": "안녕하세요"}]
    session.duration = 1.5
    save_session(session)

    loaded = load_session(session.id)
    assert loaded is not None
    assert loaded.status == "completed"
    assert loaded.speaker_names == {"1": "화자 1", "2": "화자 2"}
    assert len(loaded.segments) == 1
    assert loaded.segments[0]["original"] == "xin chào"
    assert loaded.duration == 1.5


def test_list_sessions_sorted_by_date(tmp_path):
    audio = _make_audio(tmp_path)

    s1 = create_session("first.m4a", audio, "ko")
    time.sleep(0.01)
    s2 = create_session("second.m4a", audio, "ko")

    sessions = list_sessions()
    assert len(sessions) == 2
    assert sessions[0].id == s2.id  # 최신이 먼저
    assert sessions[1].id == s1.id


def test_delete_session_removes_directory(tmp_path):
    audio = _make_audio(tmp_path)
    session = create_session("test.m4a", audio, "ko")

    session_dir = tmp_path / session.id
    assert session_dir.exists()

    delete_session(session.id)
    assert not session_dir.exists()


def test_load_nonexistent_returns_none():
    result = load_session("nonexistent-id")
    assert result is None


def test_checkpoint_fields_roundtrip(tmp_path):
    audio = _make_audio(tmp_path)
    session = create_session("test.m4a", audio, "ko")

    session.cp_segments = [{"start": 0.0, "end": 1.0, "text": "xin chào", "speaker": "1"}]
    session.cp_corrected_segments = [{"index": 0, "corrected": "xin chào", "translated": "안녕하세요"}]
    session.cp_last_chunk_done = 2
    session.cp_ctx_summary = "인사 나눔"
    session.cp_ctx_recent_pairs = [["xin chào", "안녕하세요"]]
    save_session(session)

    loaded = load_session(session.id)
    assert loaded is not None
    assert loaded.cp_segments == session.cp_segments
    assert loaded.cp_corrected_segments == session.cp_corrected_segments
    assert loaded.cp_last_chunk_done == 2
    assert loaded.cp_ctx_summary == "인사 나눔"
    assert loaded.cp_ctx_recent_pairs == [["xin chào", "안녕하세요"]]


def test_checkpoint_fields_default_values(tmp_path):
    audio = _make_audio(tmp_path)
    session = create_session("test.m4a", audio, "ko")

    loaded = load_session(session.id)
    assert loaded is not None
    assert loaded.cp_segments is None
    assert loaded.cp_corrected_segments == []
    assert loaded.cp_last_chunk_done == -1
    assert loaded.cp_ctx_summary == ""
    assert loaded.cp_ctx_recent_pairs == []
