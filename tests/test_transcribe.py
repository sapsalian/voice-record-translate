from unittest.mock import MagicMock, patch

from vrt.transcribe import Segment, _group_to_segment, _tokens_to_segments, transcribe


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
    client.stt.transcribe.return_value = MagicMock(id="tx-1")
    client.stt.wait.return_value = None
    client.stt.get_transcript.return_value = MagicMock(tokens=tokens)
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


# ── transcribe() ──────────────────────────────────────────────────────────────

def test_transcribe_returns_segments(tmp_path):
    f = str(tmp_path / "test.mp3")
    open(f, "wb").close()

    tokens = [
        _tok("xin chào", 0, 500, "1"),
        _tok("cảm ơn", 600, 1000, "2"),
    ]

    with patch("vrt.transcribe.SonioxClient") as mock_cls:
        mock_cls.return_value = _mock_client(tokens)
        result = transcribe(f, "sk-fake", language="vi")

    assert len(result) == 2
    assert result[0].text == "xin chào"
    assert result[0].speaker == "1"
    assert result[1].speaker == "2"


def test_transcribe_empty_response(tmp_path):
    f = str(tmp_path / "test.mp3")
    open(f, "wb").close()

    with patch("vrt.transcribe.SonioxClient") as mock_cls:
        mock_cls.return_value = _mock_client([])
        result = transcribe(f, "sk-fake")

    assert result == []


def test_transcribe_calls_wait_and_get_transcript(tmp_path):
    f = str(tmp_path / "test.mp3")
    open(f, "wb").close()

    with patch("vrt.transcribe.SonioxClient") as mock_cls:
        client = _mock_client([])
        mock_cls.return_value = client
        transcribe(f, "sk-fake")

    client.stt.wait.assert_called_once_with("tx-1", timeout_sec=600)
    client.stt.get_transcript.assert_called_once_with("tx-1")
