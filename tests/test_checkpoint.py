import json
from pathlib import Path

import pytest

from vrt.checkpoint import (
    Checkpoint,
    checkpoint_path,
    delete_checkpoint,
    load_checkpoint,
    save_checkpoint,
)


def test_checkpoint_path(tmp_path):
    f = str(tmp_path / "call.m4a")
    assert checkpoint_path(f) == tmp_path / "call.vrt_checkpoint.json"


def test_load_nonexistent(tmp_path):
    assert load_checkpoint(str(tmp_path / "missing.m4a")) is None


def test_save_load_roundtrip(tmp_path):
    f = str(tmp_path / "call.m4a")
    corrected = [{"index": 0, "corrected": "xin chào", "translated": "안녕하세요"}]
    cp = Checkpoint(
        file_path=f,
        target_lang="ko",
        segments=[{"start": 0.0, "end": 1.0, "text": "xin chào"}],
        corrected_segments=corrected,
        last_chunk_done=0,
        ctx_summary="인사 나눔",
        ctx_recent_pairs=[["xin chào", "안녕하세요"]],
    )
    save_checkpoint(cp)

    loaded = load_checkpoint(f)
    assert loaded is not None
    assert loaded.file_path == f
    assert loaded.target_lang == "ko"
    assert loaded.segments == [{"start": 0.0, "end": 1.0, "text": "xin chào"}]
    assert loaded.corrected_segments == corrected
    assert loaded.last_chunk_done == 0
    assert loaded.ctx_summary == "인사 나눔"
    assert loaded.ctx_recent_pairs == [["xin chào", "안녕하세요"]]


def test_delete(tmp_path):
    f = str(tmp_path / "call.m4a")
    save_checkpoint(Checkpoint(file_path=f, target_lang="ko"))
    assert checkpoint_path(f).exists()
    delete_checkpoint(f)
    assert not checkpoint_path(f).exists()


def test_delete_nonexistent_is_noop(tmp_path):
    delete_checkpoint(str(tmp_path / "missing.m4a"))


def test_save_creates_valid_json(tmp_path):
    f = str(tmp_path / "call.m4a")
    cp = Checkpoint(file_path=f, target_lang="ko")
    save_checkpoint(cp)
    data = json.loads(checkpoint_path(f).read_text(encoding="utf-8"))
    assert "source_lang" not in data
    assert data["target_lang"] == "ko"
    assert data["segments"] is None
    assert data["last_chunk_done"] == -1


def test_load_ignores_old_source_lang_field(tmp_path):
    """구 형식 체크포인트(source_lang 포함)를 로드해도 오류 없이 무시."""
    f = str(tmp_path / "call.m4a")
    p = checkpoint_path(f)
    p.write_text(
        json.dumps({"file_path": str(f), "source_lang": "vi", "target_lang": "ko"}),
        encoding="utf-8",
    )
    loaded = load_checkpoint(str(f))
    assert loaded is not None
    assert loaded.target_lang == "ko"
