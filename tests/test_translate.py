from unittest.mock import MagicMock, patch

import pytest

from vrt.transcribe import Segment
from vrt.translate import (
    TranslationItem,
    TranslationResult,
    TranslatedSegment,
    _validate_and_normalize,
    translate,
)


# ── _validate_and_normalize 단위 테스트 ──────────────────────────────────────

def _items(*pairs):
    """Helper: [(index, text), ...] → list[TranslationItem]"""
    return [TranslationItem(index=i, translated=t) for i, t in pairs]


def test_validate_normalize_happy_path():
    items = _items((1, "안녕하세요"), (2, "잘 지내세요"))
    result = _validate_and_normalize(items, 2)
    assert result == ["안녕하세요", "잘 지내세요"]


def test_validate_normalize_out_of_order():
    # GPT가 순서를 바꿔 돌려줘도 index로 정렬
    items = _items((2, "잘 지내세요"), (1, "안녕하세요"))
    result = _validate_and_normalize(items, 2)
    assert result == ["안녕하세요", "잘 지내세요"]


def test_validate_normalize_wrong_count():
    items = _items((1, "하나"))
    with pytest.raises(ValueError, match="expected 2"):
        _validate_and_normalize(items, 2)


def test_validate_normalize_duplicate_index():
    items = _items((1, "하나"), (1, "중복"))
    with pytest.raises(ValueError, match="Duplicate index 1"):
        _validate_and_normalize(items, 2)


def test_validate_normalize_out_of_range_index():
    items = _items((1, "하나"), (3, "범위초과"))
    with pytest.raises(ValueError, match="Invalid index 3"):
        _validate_and_normalize(items, 2)


def test_validate_normalize_empty_translation():
    items = _items((1, "   "), (2, "이"))
    with pytest.raises(ValueError, match="Empty translation at index 1"):
        _validate_and_normalize(items, 2)


# ── translate() 통합 테스트 (API mock) ──────────────────────────────────────

def _mock_resp(items):
    parsed = TranslationResult(items=[TranslationItem(index=i, translated=t) for i, t in items])
    resp = MagicMock()
    resp.output_parsed = parsed
    return resp


def test_translate_returns_empty_for_no_segments():
    result = translate([], "vi", "ko", "sk-fake")
    assert result == []


def test_translate_happy_path():
    segments = [
        Segment(start=0.0, end=1.0, text="Xin chào."),
        Segment(start=1.0, end=2.0, text="Bạn có khỏe không?"),
    ]

    with patch("vrt.translate.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.responses.parse.return_value = _mock_resp(
            [(1, "안녕하세요."), (2, "잘 지내세요?")]
        )

        result = translate(segments, "vi", "ko", "sk-fake")

    assert len(result) == 2
    assert result[0].original == "Xin chào."
    assert result[0].translated == "안녕하세요."
    assert result[0].start == 0.0
    assert result[1].translated == "잘 지내세요?"


def test_translate_raises_on_mismatch():
    segments = [Segment(start=0.0, end=1.0, text="Hello")]

    with patch("vrt.translate.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        # API returns 2 items but we expect 1
        mock_client.responses.parse.return_value = _mock_resp(
            [(1, "안녕"), (2, "여분")]
        )

        with pytest.raises(ValueError, match="expected 1"):
            translate(segments, "vi", "ko", "sk-fake")
