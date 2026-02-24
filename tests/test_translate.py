from unittest.mock import MagicMock, patch

import pytest

from vrt.transcribe import Segment
from vrt.translate import (
    ChunkResult,
    TranslationItem,
    TranslatedSegment,
    _collect,
    translate,
)


# ── 헬퍼 ────────────────────────────────────────────────────────────────────

def _items(*pairs):
    return [TranslationItem(index=i, translated=t) for i, t in pairs]


def _chunk_resp(summary="요약", *pairs):
    parsed = ChunkResult(
        items=[TranslationItem(index=i, translated=t) for i, t in pairs],
        summary=summary,
    )
    resp = MagicMock()
    resp.output_parsed = parsed
    return resp


def _segments(*texts):
    return [Segment(start=float(i), end=float(i + 1), text=t) for i, t in enumerate(texts)]


# ── _collect 단위 테스트 ──────────────────────────────────────────────────────

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


# ── translate() - 단일 청크 (100개 미만) ─────────────────────────────────────

def test_translate_empty():
    assert translate([], "vi", "ko", "sk-fake") == []


def test_translate_success_no_retry():
    segs = _segments("Xin chào.", "Bạn có khỏe không?")

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.return_value = _chunk_resp(
            "인사 나눔", (1, "안녕하세요."), (2, "잘 지내세요?")
        )

        result = translate(segs, "vi", "ko", "sk-fake")

    assert client.responses.parse.call_count == 1
    assert result[0].translated == "안녕하세요."
    assert result[1].translated == "잘 지내세요?"


def test_translate_retry_on_missing():
    segs = _segments("Xin chào.", "Bạn có khỏe không?")

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.side_effect = [
            _chunk_resp("인사", (1, "안녕하세요.")),          # 1차: index 2 누락
            _chunk_resp("재시도", (1, "잘 지내세요?")),        # 2차: 누락분 재전송
        ]

        result = translate(segs, "vi", "ko", "sk-fake")

    assert client.responses.parse.call_count == 2
    assert result[0].translated == "안녕하세요."
    assert result[1].translated == "잘 지내세요?"


def test_translate_fallback_on_persistent_failure():
    """재시도 후에도 실패한 세그먼트는 [번역실패] 접두사 + 원문으로 대체 (예외 없음)."""
    segs = _segments("Xin chào.", "Bạn có khỏe không?")

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.side_effect = [
            _chunk_resp("인사", (1, "안녕하세요.")),
            _chunk_resp("재시도"),                             # 여전히 누락
        ]

        result = translate(segs, "vi", "ko", "sk-fake")

    assert result[0].translated == "안녕하세요."
    assert result[1].translated == "[번역실패] Bạn có khỏe không?"


def test_translate_timestamps_preserved():
    segs = [Segment(start=1.5, end=3.0, text="Hello")]

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.return_value = _chunk_resp("인사", (1, "안녕"))

        result = translate(segs, "en", "ko", "sk-fake")

    assert result[0].start == 1.5
    assert result[0].end == 3.0
    assert result[0].original == "Hello"


# ── translate() - 다중 청크 ───────────────────────────────────────────────────

def test_translate_two_chunks():
    """150개 세그먼트 → 청크 2개(100 + 50), API 2회 호출."""
    segs = _segments(*[f"text_{i}" for i in range(150)])

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client

        def make_chunk_resp(chunk_segs):
            return _chunk_resp(
                "요약",
                *[(i + 1, f"번역_{i}") for i in range(len(chunk_segs))]
            )

        client.responses.parse.side_effect = [
            make_chunk_resp(segs[:100]),
            make_chunk_resp(segs[100:]),
        ]

        result = translate(segs, "vi", "ko", "sk-fake")

    assert client.responses.parse.call_count == 2
    assert len(result) == 150
    assert result[0].translated == "번역_0"
    assert result[99].translated == "번역_99"
    assert result[100].translated == "번역_0"   # 2번째 청크 내 index 1
    assert result[149].translated == "번역_49"


def test_translate_progress_callback():
    """progress_callback이 청크 완료 시마다 호출되는지 확인."""
    segs = _segments(*[f"t_{i}" for i in range(150)])
    calls = []

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.side_effect = [
            _chunk_resp("요약", *[(i + 1, f"번_{i}") for i in range(100)]),
            _chunk_resp("요약", *[(i + 1, f"번_{i}") for i in range(50)]),
        ]

        translate(segs, "vi", "ko", "sk-fake", progress_callback=lambda d, t: calls.append((d, t)))

    assert calls == [(1, 2), (2, 2)]


def test_translate_second_chunk_gets_context():
    """2번째 청크 API 호출 시 system prompt에 이전 요약이 포함되는지 확인."""
    segs = _segments(*[f"t_{i}" for i in range(110)])

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.side_effect = [
            _chunk_resp("첫 청크 요약", *[(i + 1, f"번_{i}") for i in range(100)]),
            _chunk_resp("두번째 요약", *[(i + 1, f"번_{i}") for i in range(10)]),
        ]

        translate(segs, "vi", "ko", "sk-fake")

    # 2번째 호출의 system prompt에 요약이 포함되어야 함
    second_call_args = client.responses.parse.call_args_list[1]
    system_content = second_call_args.kwargs["input"][0]["content"]
    assert "첫 청크 요약" in system_content


# ── translate() - resume (start_chunk) ───────────────────────────────────────

def test_translate_resume_skips_done_chunks():
    """start_chunk=1이면 청크 0은 skip, API는 1회만 호출."""
    segs = _segments(*[f"t_{i}" for i in range(110)])
    already = {i + 1: f"번_{i}" for i in range(100)}  # 청크 0 결과

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.return_value = _chunk_resp(
            "요약", *[(i + 1, f"번_{i}") for i in range(10)]
        )

        result = translate(
            segs, "vi", "ko", "sk-fake",
            start_chunk=1,
            initial_collected=already,
        )

    assert client.responses.parse.call_count == 1
    assert len(result) == 110
    assert result[0].translated == "번_0"    # 청크 0 결과 (initial_collected)
    assert result[100].translated == "번_0"  # 청크 1 결과


def test_translate_on_chunk_done_called():
    """on_chunk_done 콜백이 청크 완료마다 호출되는지 확인."""
    segs = _segments(*[f"t_{i}" for i in range(150)])
    calls = []

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.side_effect = [
            _chunk_resp("요약1", *[(i + 1, f"번_{i}") for i in range(100)]),
            _chunk_resp("요약2", *[(i + 1, f"번_{i}") for i in range(50)]),
        ]

        translate(
            segs, "vi", "ko", "sk-fake",
            on_chunk_done=lambda idx, collected, ctx: calls.append((idx, len(collected), ctx.summary)),
        )

    assert calls[0] == (0, 100, "요약1")
    assert calls[1] == (1, 150, "요약2")
