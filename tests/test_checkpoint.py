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
    corrected = [{"start": 0.0, "end": 1.0, "corrected": "xin chào", "translated": "안녕하세요"}]
    cp = Checkpoint(
        file_path=f,
        source_lang="vi",
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
    assert loaded.source_lang == "vi"
    assert loaded.segments == [{"start": 0.0, "end": 1.0, "text": "xin chào"}]
    assert loaded.corrected_segments == corrected
    assert loaded.last_chunk_done == 0
    assert loaded.ctx_summary == "인사 나눔"
    assert loaded.ctx_recent_pairs == [["xin chào", "안녕하세요"]]


def test_delete(tmp_path):
    f = str(tmp_path / "call.m4a")
    save_checkpoint(Checkpoint(file_path=f, source_lang="vi", target_lang="ko"))
    assert checkpoint_path(f).exists()
    delete_checkpoint(f)
    assert not checkpoint_path(f).exists()


def test_delete_nonexistent_is_noop(tmp_path):
    # 없는 파일 삭제 시 예외 없이 통과
    delete_checkpoint(str(tmp_path / "missing.m4a"))


def test_save_creates_valid_json(tmp_path):
    f = str(tmp_path / "call.m4a")
    cp = Checkpoint(file_path=f, source_lang="vi", target_lang="ko")
    save_checkpoint(cp)
    data = json.loads(checkpoint_path(f).read_text(encoding="utf-8"))
    assert data["source_lang"] == "vi"
    assert data["segments"] is None
    assert data["last_chunk_done"] == -1
