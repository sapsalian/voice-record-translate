from unittest.mock import MagicMock, call, patch

import pytest

from vrt.transcribe import Segment
from vrt.translate import (
    TranslationItem,
    TranslationResult,
    TranslatedSegment,
    _collect,
    translate,
)


# ── _collect 단위 테스트 ──────────────────────────────────────────────────────

def _items(*pairs):
    return [TranslationItem(index=i, translated=t) for i, t in pairs]


def test_collect_happy_path():
    result = _collect(_items((1, "안녕"), (2, "잘 지내")), 2)
    assert result == {1: "안녕", 2: "잘 지내"}


def test_collect_out_of_order():
    result = _collect(_items((2, "잘 지내"), (1, "안녕")), 2)
    assert result == {1: "안녕", 2: "잘 지내"}


def test_collect_out_of_range_ignored():
    result = _collect(_items((1, "하나"), (3, "범위초과")), 2)
    assert result == {1: "하나"}


def test_collect_duplicate_keeps_first():
    result = _collect(_items((1, "첫번째"), (1, "중복")), 2)
    assert result == {1: "첫번째"}


def test_collect_empty_translation_ignored():
    result = _collect(_items((1, "   "), (2, "이")), 2)
    assert result == {2: "이"}


def test_collect_partial_result():
    result = _collect(_items((1, "하나")), 3)
    assert result == {1: "하나"}
    assert 2 not in result
    assert 3 not in result


# ── translate() 통합 테스트 (API mock) ───────────────────────────────────────

def _make_resp(*pairs):
    parsed = TranslationResult(items=[TranslationItem(index=i, translated=t) for i, t in pairs])
    resp = MagicMock()
    resp.output_parsed = parsed
    return resp


def _segments(*texts):
    return [Segment(start=float(i), end=float(i + 1), text=t) for i, t in enumerate(texts)]


def test_translate_empty():
    assert translate([], "vi", "ko", "sk-fake") == []


def test_translate_success_no_retry():
    segs = _segments("Xin chào.", "Bạn có khỏe không?")

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.return_value = _make_resp((1, "안녕하세요."), (2, "잘 지내세요?"))

        result = translate(segs, "vi", "ko", "sk-fake")

    assert client.responses.parse.call_count == 1
    assert result[0].translated == "안녕하세요."
    assert result[1].translated == "잘 지내세요?"


def test_translate_retry_on_missing():
    """1차에서 index 2가 누락 → 2차에서 index 2만 재전송 → 성공."""
    segs = _segments("Xin chào.", "Bạn có khỏe không?")

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.side_effect = [
            _make_resp((1, "안녕하세요.")),          # 1차: index 2 누락
            _make_resp((1, "잘 지내세요?")),          # 2차: 누락된 것만 재전송, index 1로 매핑됨
        ]

        result = translate(segs, "vi", "ko", "sk-fake")

    assert client.responses.parse.call_count == 2
    assert result[0].translated == "안녕하세요."
    assert result[1].translated == "잘 지내세요?"


def test_translate_raises_if_retry_also_fails():
    """재시도 후에도 누락이 있으면 ValueError."""
    segs = _segments("Xin chào.", "Bạn có khỏe không?")

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.side_effect = [
            _make_resp((1, "안녕하세요.")),   # 1차: index 2 누락
            _make_resp(),                     # 2차: 여전히 없음
        ]

        with pytest.raises(ValueError, match="번역 실패한 세그먼트 인덱스"):
            translate(segs, "vi", "ko", "sk-fake")

    assert client.responses.parse.call_count == 2


def test_translate_timestamps_preserved():
    segs = [Segment(start=1.5, end=3.0, text="Hello")]

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.return_value = _make_resp((1, "안녕"))

        result = translate(segs, "en", "ko", "sk-fake")

    assert result[0].start == 1.5
    assert result[0].end == 3.0
    assert result[0].original == "Hello"
