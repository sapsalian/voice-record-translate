import pytest
from unittest.mock import MagicMock, patch

from vrt.transcribe import (
    CHUNK_MAX_SEC,
    Segment,
    _get_duration,
    _group_to_segment,
    _tokens_to_segments,
    _transcribe_file,
    transcribe,
)


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


def _mock_av_container(duration_sec):
    container = MagicMock()
    container.duration = int(duration_sec * 1_000_000) if duration_sec is not None else None
    container.__enter__ = lambda s: s
    container.__exit__ = MagicMock(return_value=False)
    return container


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


# ── _get_duration ─────────────────────────────────────────────────────────────

def test_get_duration_returns_seconds(tmp_path):
    f = str(tmp_path / "test.mp3")
    with patch("vrt.transcribe.av.open", return_value=_mock_av_container(3600)):
        assert _get_duration(f) == pytest.approx(3600.0)


def test_get_duration_returns_none_when_unknown(tmp_path):
    f = str(tmp_path / "test.mp3")
    with patch("vrt.transcribe.av.open", return_value=_mock_av_container(None)):
        assert _get_duration(f) is None


# ── transcribe() ──────────────────────────────────────────────────────────────

def test_transcribe_returns_segments(tmp_path):
    f = str(tmp_path / "test.mp3")
    open(f, "wb").close()

    tokens = [
        _tok("xin chào", 0, 500, "1"),
        _tok("cảm ơn", 600, 1000, "2"),
    ]

    with patch("vrt.transcribe._get_duration", return_value=None), \
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

    with patch("vrt.transcribe._get_duration", return_value=None), \
         patch("vrt.transcribe.SonioxClient") as mock_cls:
        mock_cls.return_value = _mock_client([])
        result = transcribe(f, "sk-fake")

    assert result == []


def test_transcribe_uses_delete_after(tmp_path):
    """transcribe_and_wait_with_tokens에 delete_after=True가 전달되는지 확인."""
    f = str(tmp_path / "test.mp3")
    open(f, "wb").close()

    with patch("vrt.transcribe._get_duration", return_value=None), \
         patch("vrt.transcribe.SonioxClient") as mock_cls:
        client = _mock_client([])
        mock_cls.return_value = client
        transcribe(f, "sk-fake")

    call_kwargs = client.stt.transcribe_and_wait_with_tokens.call_args.kwargs
    assert call_kwargs["delete_after"] is True
    assert call_kwargs["wait_timeout_sec"] == 3_600


# ── 청크 분할 ──────────────────────────────────────────────────────────────────

def test_transcribe_short_file_uses_single_call(tmp_path):
    """150분 이하 → _transcribe_file 1회 호출 (분할 없음)."""
    f = str(tmp_path / "short.mp3")
    open(f, "wb").close()

    with patch("vrt.transcribe._get_duration", return_value=float(CHUNK_MAX_SEC)), \
         patch("vrt.transcribe._transcribe_file", return_value=[]) as mock_tf:
        transcribe(f, "sk-fake")

    mock_tf.assert_called_once_with(f, "sk-fake")


def test_transcribe_long_file_splits_into_two_chunks(tmp_path):
    """180분 파일 → 2청크, 두 번째 청크 offset=9000 적용."""
    f = str(tmp_path / "long.mp3")
    open(f, "wb").close()

    call_count = 0

    def mock_transcribe_file(path, api_key, offset=0.0):
        nonlocal call_count
        call_count += 1
        seg = Segment(0.0, 5.0, "word", "1")
        return [Segment(seg.start + offset, seg.end + offset, seg.text, seg.speaker)]

    with patch("vrt.transcribe._get_duration", return_value=10_800.0), \
         patch("vrt.transcribe._split_audio", return_value=[("/c1.mp3", 0.0), ("/c2.mp3", 9_000.0)]), \
         patch("vrt.transcribe._transcribe_file", side_effect=mock_transcribe_file):
        result = transcribe(f, "sk-fake")

    assert call_count == 2
    assert result[0].start == 0.0
    assert result[1].start == 9_000.0


def test_transcribe_chunked_remaps_speaker_ids(tmp_path):
    """청크별 화자 ID가 겹치지 않도록 재매핑됨."""
    f = str(tmp_path / "long.mp3")
    open(f, "wb").close()

    chunk1 = [Segment(0.0, 5.0, "a", "1"), Segment(5.0, 10.0, "b", "2")]
    chunk2 = [Segment(0.0, 5.0, "c", "1")]  # 다른 사람인 화자 "1"

    call_returns = [chunk1, chunk2]

    with patch("vrt.transcribe._get_duration", return_value=10_800.0), \
         patch("vrt.transcribe._split_audio", return_value=[("/c1.mp3", 0.0), ("/c2.mp3", 9_000.0)]), \
         patch("vrt.transcribe._transcribe_file", side_effect=lambda *a, **kw: call_returns.pop(0)):
        result = transcribe(f, "sk-fake")

    assert result[0].speaker == "1"
    assert result[1].speaker == "2"
    assert result[2].speaker == "3"   # 청크 2의 "1" → "3"으로 재매핑


def test_transcribe_progress_callback_called_per_chunk(tmp_path):
    """청크 분할 전사 시 progress_callback이 청크마다 호출됨."""
    f = str(tmp_path / "long.mp3")
    open(f, "wb").close()

    calls = []
    chunks = [Segment(0.0, 5.0, "a", "1")]
    with patch("vrt.transcribe._get_duration", return_value=10_800.0), \
         patch("vrt.transcribe._split_audio", return_value=[("/c1.mp3", 0.0), ("/c2.mp3", 9_000.0)]), \
         patch("vrt.transcribe._transcribe_file", return_value=chunks):
        transcribe(f, "sk-fake", progress_callback=lambda done, total: calls.append((done, total)))

    assert calls == [(1, 2), (2, 2)]


def test_transcribe_no_callback_for_single_file(tmp_path):
    """단일 파일(분할 없음)은 progress_callback 미호출."""
    f = str(tmp_path / "short.mp3")
    open(f, "wb").close()

    calls = []
    with patch("vrt.transcribe._get_duration", return_value=float(CHUNK_MAX_SEC)), \
         patch("vrt.transcribe._transcribe_file", return_value=[]):
        transcribe(f, "sk-fake", progress_callback=lambda done, total: calls.append((done, total)))

    assert calls == []
