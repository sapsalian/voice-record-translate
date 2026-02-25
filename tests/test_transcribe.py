import pytest
from unittest.mock import MagicMock, patch

from vrt.transcribe import Segment, _check_duration, _group_to_segment, _tokens_to_segments, transcribe


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def _tok(text, start_ms, end_ms, speaker="1"):
    t = MagicMock()
    t.text = text
    t.start_ms = start_ms
    t.end_ms = end_ms
    t.speaker = speaker
    return t


def _mock_client(tokens):
    client = MagicMock()
    client.stt.transcribe_and_wait_with_tokens.return_value = MagicMock(tokens=tokens)
    return client


# ── _tokens_to_segments ───────────────────────────────────────────────────────

def test_tokens_to_segments_empty():
    assert _tokens_to_segments([]) == []


def test_tokens_to_segments_single_speaker():
    tokens = [
        _tok("xin", 0, 300, "1"),
        _tok("chào", 300, 600, "1"),
    ]
    result = _tokens_to_segments(tokens)
    assert len(result) == 1
    assert result[0].start == 0.0
    assert result[0].end == 0.6
    assert result[0].text == "xin chào"
    assert result[0].speaker == "1"


def test_tokens_to_segments_speaker_split():
    tokens = [
        _tok("xin chào", 0, 500, "1"),
        _tok("cảm ơn", 600, 1000, "2"),
    ]
    result = _tokens_to_segments(tokens)
    assert len(result) == 2
    assert result[0].speaker == "1"
    assert result[0].text == "xin chào"
    assert result[1].speaker == "2"
    assert result[1].text == "cảm ơn"


def test_tokens_to_segments_skips_blank_tokens():
    tokens = [
        _tok("hello", 0, 300, "1"),
        _tok("  ", 300, 400, "1"),  # 공백 → 무시
        _tok("world", 400, 700, "1"),
    ]
    result = _tokens_to_segments(tokens)
    assert len(result) == 1
    assert result[0].text == "hello world"


def test_tokens_to_segments_none_timestamps():
    tokens = [_tok("hello", None, None, "1")]
    result = _tokens_to_segments(tokens)
    assert len(result) == 1
    assert result[0].start == 0.0
    assert result[0].end == 0.0


def test_tokens_to_segments_three_speakers():
    tokens = [
        _tok("a", 0, 100, "1"),
        _tok("b", 200, 300, "2"),
        _tok("c", 400, 500, "1"),  # 화자 1이 다시 등장 → 새 세그먼트
    ]
    result = _tokens_to_segments(tokens)
    assert len(result) == 3
    assert result[0].speaker == "1"
    assert result[1].speaker == "2"
    assert result[2].speaker == "1"


# ── _group_to_segment ─────────────────────────────────────────────────────────

def test_group_to_segment_basic():
    tokens = [_tok("xin", 0, 300, "1"), _tok("chào", 300, 600, "1")]
    seg = _group_to_segment(tokens, "1")
    assert seg.start == 0.0
    assert seg.end == 0.6
    assert seg.text == "xin chào"
    assert seg.speaker == "1"


# ── _check_duration ───────────────────────────────────────────────────────────

def _mock_av_container(duration_sec):
    container = MagicMock()
    container.duration = int(duration_sec * 1_000_000) if duration_sec is not None else None
    container.__enter__ = lambda s: s
    container.__exit__ = MagicMock(return_value=False)
    return container


def test_check_duration_accepts_short_file(tmp_path):
    f = str(tmp_path / "short.mp3")
    with patch("vrt.transcribe.av.open", return_value=_mock_av_container(3600)):  # 60분
        _check_duration(f)  # 예외 없음


def test_check_duration_rejects_long_file(tmp_path):
    f = str(tmp_path / "long.mp3")
    with patch("vrt.transcribe.av.open", return_value=_mock_av_container(18_001)):  # 300분 1초
        with pytest.raises(ValueError, match="300분"):
            _check_duration(f)


def test_check_duration_skips_when_unknown(tmp_path):
    f = str(tmp_path / "unknown.mp3")
    with patch("vrt.transcribe.av.open", return_value=_mock_av_container(None)):
        _check_duration(f)  # duration=None → 예외 없음


# ── transcribe() ──────────────────────────────────────────────────────────────

def test_transcribe_returns_segments(tmp_path):
    f = str(tmp_path / "test.mp3")
    open(f, "wb").close()

    tokens = [
        _tok("xin chào", 0, 500, "1"),
        _tok("cảm ơn", 600, 1000, "2"),
    ]

    with patch("vrt.transcribe._check_duration"), \
         patch("vrt.transcribe.SonioxClient") as mock_cls:
        mock_cls.return_value = _mock_client(tokens)
        result = transcribe(f, "sk-fake")

    assert len(result) == 2
    assert result[0].text == "xin chào"
    assert result[0].speaker == "1"
    assert result[1].speaker == "2"


def test_transcribe_empty_response(tmp_path):
    f = str(tmp_path / "test.mp3")
    open(f, "wb").close()

    with patch("vrt.transcribe._check_duration"), \
         patch("vrt.transcribe.SonioxClient") as mock_cls:
        mock_cls.return_value = _mock_client([])
        result = transcribe(f, "sk-fake")

    assert result == []


def test_transcribe_uses_delete_after(tmp_path):
    """transcribe_and_wait_with_tokens에 delete_after=True가 전달되는지 확인."""
    f = str(tmp_path / "test.mp3")
    open(f, "wb").close()

    with patch("vrt.transcribe._check_duration"), \
         patch("vrt.transcribe.SonioxClient") as mock_cls:
        client = _mock_client([])
        mock_cls.return_value = client
        transcribe(f, "sk-fake")

    call_kwargs = client.stt.transcribe_and_wait_with_tokens.call_args.kwargs
    assert call_kwargs["delete_after"] is True
    assert call_kwargs["wait_timeout_sec"] == 600
