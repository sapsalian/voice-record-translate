from unittest.mock import MagicMock, patch

from vrt.transcribe import Segment
from vrt.translate import (
    CorrectedSegment,
    CorrectionResult,
    translate,
)


# ── 헬퍼 ────────────────────────────────────────────────────────────────────

def _seg(start, end, corrected, translated):
    return CorrectedSegment(start=start, end=end, corrected=corrected, translated=translated)


def _chunk_resp(summary="요약", *segs):
    parsed = CorrectionResult(segments=list(segs), summary=summary)
    resp = MagicMock()
    resp.output_parsed = parsed
    return resp


def _segments(*texts):
    return [Segment(start=float(i), end=float(i + 1), text=t) for i, t in enumerate(texts)]


# ── translate() - 단일 청크 ───────────────────────────────────────────────

def test_translate_empty():
    assert translate([], "vi", "ko", "sk-fake") == []


def test_translate_success_no_retry():
    segs = _segments("Xin chào.", "Bạn có khỏe không?")

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.return_value = _chunk_resp(
            "인사 나눔",
            _seg(0.0, 1.0, "Xin chào.", "안녕하세요."),
            _seg(1.0, 2.0, "Bạn có khỏe không?", "잘 지내세요?"),
        )

        result = translate(segs, "vi", "ko", "sk-fake")

    assert client.responses.parse.call_count == 1
    assert result[0].translated == "안녕하세요."
    assert result[1].translated == "잘 지내세요?"


def test_translate_retry_on_empty():
    """첫 응답이 빈 segments → 1회 재시도."""
    segs = _segments("Xin chào.", "Bạn có khỏe không?")

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.side_effect = [
            _chunk_resp("인사"),  # 빈 segments → retry
            _chunk_resp(
                "재시도",
                _seg(0.0, 1.0, "Xin chào.", "안녕하세요."),
                _seg(1.0, 2.0, "Bạn có khỏe không?", "잘 지내세요?"),
            ),
        ]

        result = translate(segs, "vi", "ko", "sk-fake")

    assert client.responses.parse.call_count == 2
    assert result[0].translated == "안녕하세요."
    assert result[1].translated == "잘 지내세요?"


def test_translate_fallback_on_persistent_failure():
    """재시도 후에도 빈 segments → [번역실패] 접두사 + 원문 (예외 없음)."""
    segs = _segments("Xin chào.", "Bạn có khỏe không?")

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.side_effect = [
            _chunk_resp("인사"),   # 빈 segments
            _chunk_resp("재시도"), # 여전히 빈 segments
        ]

        result = translate(segs, "vi", "ko", "sk-fake")

    assert result[0].translated == "[번역실패] Xin chào."
    assert result[1].translated == "[번역실패] Bạn có khỏe không?"


def test_translate_timestamps_preserved():
    segs = [Segment(start=1.5, end=3.0, text="Hello")]

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.return_value = _chunk_resp(
            "인사",
            _seg(1.5, 3.0, "Hello", "안녕"),
        )

        result = translate(segs, "en", "ko", "sk-fake")

    assert result[0].start == 1.5
    assert result[0].end == 3.0
    assert result[0].original == "Hello"


def test_correct_and_translate_merges_segments():
    """GPT가 세그먼트를 병합하면 출력 수가 입력 수보다 적어짐."""
    segs = _segments("안녕하", "세요")  # 2개 입력

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.return_value = _chunk_resp(
            "인사",
            _seg(0.0, 2.0, "안녕하세요", "Hello"),  # 1개 출력 (병합)
        )

        result = translate(segs, "ko", "en", "sk-fake")

    assert len(result) == 1
    assert result[0].start == 0.0
    assert result[0].end == 2.0
    assert result[0].original == "안녕하세요"
    assert result[0].translated == "Hello"


# ── translate() - 다중 청크 ───────────────────────────────────────────────

def test_translate_two_chunks():
    """150개 세그먼트 → 청크 2개(100 + 50), API 2회 호출."""
    segs = _segments(*[f"text_{i}" for i in range(150)])

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client

        def make_chunk_resp(chunk_segs):
            return _chunk_resp(
                "요약",
                *[_seg(s.start, s.end, s.text, f"번역_{i}") for i, s in enumerate(chunk_segs)],
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
    assert result[100].translated == "번역_0"   # 2번째 청크 내 첫번째
    assert result[149].translated == "번역_49"


def test_translate_progress_callback():
    """progress_callback이 청크 완료 시마다 호출되는지 확인."""
    segs = _segments(*[f"t_{i}" for i in range(150)])
    calls = []

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.side_effect = [
            _chunk_resp("요약", *[_seg(float(i), float(i+1), f"t_{i}", f"번_{i}") for i in range(100)]),
            _chunk_resp("요약", *[_seg(float(i), float(i+1), f"t_{i}", f"번_{i}") for i in range(50)]),
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
            _chunk_resp("첫 청크 요약", *[_seg(float(i), float(i+1), f"t_{i}", f"번_{i}") for i in range(100)]),
            _chunk_resp("두번째 요약", *[_seg(float(i), float(i+1), f"t_{i}", f"번_{i}") for i in range(10)]),
        ]

        translate(segs, "vi", "ko", "sk-fake")

    second_call_args = client.responses.parse.call_args_list[1]
    system_content = second_call_args.kwargs["input"][0]["content"]
    assert "첫 청크 요약" in system_content


# ── translate() - resume (start_chunk) ────────────────────────────────────

def test_translate_resume_skips_done_chunks():
    """start_chunk=1이면 청크 0은 skip, API는 1회만 호출."""
    segs = _segments(*[f"t_{i}" for i in range(110)])
    already = [_seg(float(i), float(i+1), f"t_{i}", f"번_{i}") for i in range(100)]

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.return_value = _chunk_resp(
            "요약",
            *[_seg(float(100+i), float(101+i), f"t_{100+i}", f"번_{i}") for i in range(10)],
        )

        result = translate(
            segs, "vi", "ko", "sk-fake",
            start_chunk=1,
            initial_corrected=already,
        )

    assert client.responses.parse.call_count == 1
    assert len(result) == 110
    assert result[0].translated == "번_0"    # 청크 0 결과 (initial_corrected)
    assert result[100].translated == "번_0"  # 청크 1 결과


def test_translate_on_chunk_done_called():
    """on_chunk_done 콜백이 청크 완료마다 호출되는지 확인."""
    segs = _segments(*[f"t_{i}" for i in range(150)])
    calls = []

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.side_effect = [
            _chunk_resp("요약1", *[_seg(float(i), float(i+1), f"t_{i}", f"번_{i}") for i in range(100)]),
            _chunk_resp("요약2", *[_seg(float(i), float(i+1), f"t_{i}", f"번_{i}") for i in range(50)]),
        ]

        translate(
            segs, "vi", "ko", "sk-fake",
            on_chunk_done=lambda idx, collected, ctx: calls.append((idx, len(collected), ctx.summary)),
        )

    assert calls[0] == (0, 100, "요약1")
    assert calls[1] == (1, 150, "요약2")


# ── speaker 보존 ────────────────────────────────────────────────────────────

def test_speaker_preserved_single_speaker():
    """단일 화자 세그먼트 2개 → GPT가 1개로 병합해도 speaker 보존."""
    from vrt.transcribe import Segment as Seg
    segs = [
        Seg(start=0.0, end=1.0, text="xin chào", speaker="1"),
        Seg(start=1.0, end=2.0, text="bạn khỏe không", speaker="1"),
    ]

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.return_value = _chunk_resp(
            "요약",
            _seg(0.0, 2.0, "xin chào bạn khỏe không", "안녕하세요 잘 지내세요"),
        )
        result = translate(segs, "vi", "ko", "sk-fake")

    assert len(result) == 1
    assert result[0].speaker == "1"


def test_speaker_preserved_two_speakers():
    """두 화자 세그먼트 → 각각 speaker 보존."""
    from vrt.transcribe import Segment as Seg
    segs = [
        Seg(start=0.0, end=1.0, text="xin chào", speaker="1"),
        Seg(start=1.5, end=2.5, text="cảm ơn", speaker="2"),
    ]

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.return_value = _chunk_resp(
            "요약",
            _seg(0.0, 1.0, "xin chào", "안녕하세요"),
            _seg(1.5, 2.5, "cảm ơn", "감사합니다"),
        )
        result = translate(segs, "vi", "ko", "sk-fake")

    assert len(result) == 2
    assert result[0].speaker == "1"
    assert result[1].speaker == "2"


def test_speaker_none_when_segment_speaker_is_none():
    """speaker=None 세그먼트 → TranslatedSegment.speaker도 None."""
    from vrt.transcribe import Segment as Seg
    segs = [Seg(start=0.0, end=1.0, text="hello", speaker=None)]

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.return_value = _chunk_resp(
            "요약",
            _seg(0.0, 1.0, "hello", "안녕"),
        )
        result = translate(segs, "en", "ko", "sk-fake")

    assert result[0].speaker is None


def test_speaker_lookup_uses_closest_timestamp():
    """GPT가 타임스탬프를 미세하게 바꿔도 0.5초 이내면 speaker 매핑."""
    from vrt.transcribe import Segment as Seg
    segs = [Seg(start=0.0, end=1.0, text="hello", speaker="1")]

    with patch("vrt.translate.OpenAI") as mock_openai:
        client = MagicMock()
        mock_openai.return_value = client
        client.responses.parse.return_value = _chunk_resp(
            "요약",
            _seg(0.3, 1.0, "hello", "안녕"),  # start가 0.3으로 미세하게 다름
        )
        result = translate(segs, "en", "ko", "sk-fake")

    assert result[0].speaker == "1"
