import json
from dataclasses import dataclass
from typing import Callable, List

from openai import OpenAI
from pydantic import BaseModel

from .transcribe import Segment

LANGUAGES = {
    "vi": "Vietnamese",
    "ko": "Korean",
    "en": "English",
    "ja": "Japanese",
    "zh": "Chinese",
}

CHUNK_SIZE = 100
CONTEXT_PAIRS = 10


@dataclass
class TranslatedSegment:
    start: float
    end: float
    original: str
    translated: str
    speaker: str | None = None


@dataclass
class _ChunkCtx:
    summary: str
    recent_pairs: list[tuple[str, str]]  # (교정된 원문, 번역) 최근 CONTEXT_PAIRS쌍


class CorrectedSegment(BaseModel):
    start: float
    end: float
    corrected: str   # 교정된 원문
    translated: str  # 번역문


class CorrectionResult(BaseModel):
    segments: list[CorrectedSegment]
    summary: str


def _lookup_speaker(start: float, speaker_map: dict) -> "str | None":
    if start in speaker_map:
        return speaker_map[start]
    candidates = [(abs(s - start), sp) for s, sp in speaker_map.items()]
    if not candidates:
        return None
    closest_diff, closest_speaker = min(candidates)
    return closest_speaker if closest_diff <= 0.5 else None


def _segment_to_dict(seg: Segment) -> dict:
    """Segment → API 전송용 dict."""
    d = {"start": seg.start, "end": seg.end, "text": seg.text}
    if seg.speaker is not None:
        d["speaker"] = seg.speaker
    return d


def translate(
    segments: List[Segment],
    source_lang: str,
    target_lang: str,
    api_key: str,
    model: str = "gpt-4.1",
    temperature: float = 0.3,
    progress_callback: Callable[[int, int], None] | None = None,
    start_chunk: int = 0,
    initial_ctx: "_ChunkCtx | None" = None,
    initial_corrected: "list[CorrectedSegment] | None" = None,
    on_chunk_done: "Callable[[int, list[CorrectedSegment], _ChunkCtx], None] | None" = None,
) -> List[TranslatedSegment]:
    if not segments:
        return []

    chunks = [segments[i:i + CHUNK_SIZE] for i in range(0, len(segments), CHUNK_SIZE)]
    total_chunks = len(chunks)
    all_corrected: list[CorrectedSegment] = list(initial_corrected or [])
    ctx: _ChunkCtx | None = initial_ctx

    for chunk_idx, chunk in enumerate(chunks):
        if chunk_idx < start_chunk:
            continue

        corrected_segs, ctx = _translate_chunk(
            chunk, source_lang, target_lang, api_key, model, temperature, ctx
        )
        all_corrected.extend(corrected_segs)

        if progress_callback:
            progress_callback(chunk_idx + 1, total_chunks)

        if on_chunk_done:
            on_chunk_done(chunk_idx, all_corrected, ctx)

    speaker_map = {seg.start: seg.speaker for seg in segments}
    return [
        TranslatedSegment(
            start=seg.start,
            end=seg.end,
            original=seg.corrected,
            translated=seg.translated,
            speaker=_lookup_speaker(seg.start, speaker_map),
        )
        for seg in all_corrected
    ]


def _translate_chunk(
    chunk: List[Segment],
    source_lang: str,
    target_lang: str,
    api_key: str,
    model: str,
    temperature: float,
    ctx: _ChunkCtx | None,
) -> tuple[list[CorrectedSegment], _ChunkCtx]:
    result = _call_api_chunk(chunk, source_lang, target_lang, api_key, model, temperature, ctx)

    if not result.segments:
        result = _call_api_chunk(chunk, source_lang, target_lang, api_key, model, temperature, ctx=None)

    if not result.segments:
        fallback = [
            CorrectedSegment(
                start=seg.start,
                end=seg.end,
                corrected=seg.text,
                translated=f"[번역실패] {seg.text}",
            )
            for seg in chunk
        ]
        return fallback, _ChunkCtx(summary=result.summary or "", recent_pairs=[])

    pairs = [(seg.corrected, seg.translated) for seg in result.segments]
    new_ctx = _ChunkCtx(
        summary=result.summary,
        recent_pairs=pairs[-CONTEXT_PAIRS:],
    )
    return result.segments, new_ctx


def _call_api_chunk(
    segments: List[Segment],
    source_lang: str,
    target_lang: str,
    api_key: str,
    model: str,
    temperature: float,
    ctx: _ChunkCtx | None,
) -> CorrectionResult:
    source_name = LANGUAGES.get(source_lang, source_lang)
    target_name = LANGUAGES.get(target_lang, target_lang)

    segments_json = json.dumps([_segment_to_dict(s) for s in segments], ensure_ascii=False)

    context_block = ""
    if ctx:
        pairs_text = "\n".join(
            f"{source_lang}: {orig} → {target_lang}: {trans}"
            for orig, trans in ctx.recent_pairs
        )
        context_block = (
            f"\n[지금까지의 누적 대화 요약]\n"
            f"{ctx.summary}\n\n"
            f"최근 번역 쌍 (참고용, 용어/어투 일관성 유지):\n{pairs_text}\n"
        )

    system_prompt = (
        f"{context_block}"
        f"[교정 및 번역 지시]\n"
        f"You are a professional translator and transcription corrector.\n"
        f"The audio is a conversation between multiple speakers.\n"
        f"You will receive a JSON array of audio segments with start/end times and transcribed text.\n"
        f"Correct the transcription and translate from {source_name} to {target_name}.\n"
        f"You MUST return JSON that matches the provided schema.\n"
        f"Rules:\n"
        f"- Each segment has a 'speaker' field identifying the speaker. "
        f"NEVER merge segments with different speaker values.\n"
        f"- Within the same speaker, merge segments that are unnaturally split mid-sentence. "
        f"Use the first segment's start and last segment's end for the merged segment.\n"
        f"- Correct transcription errors (mishearing, wrong words) based on context.\n"
        f"- start/end values must stay within the input range.\n"
        f"- corrected: the corrected source text ({source_name}).\n"
        f"- translated: the translation in {target_name}.\n"
        f"- summary: 이전 누적 요약(있다면)과 이번 청크 내용을 합쳐 전체 대화의 누적 요약을 작성. "
        f"고유명사(이름, 회사명, 지역명)와 주요 주제를 반드시 포함. 2~5문장.\n"
    )

    client = OpenAI(api_key=api_key)
    resp = client.responses.parse(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": segments_json},
        ],
        text_format=CorrectionResult,
        temperature=temperature,
    )
    parsed: CorrectionResult = resp.output_parsed  # type: ignore[attr-defined]
    if parsed is None:
        return CorrectionResult(segments=[], summary="")
    return parsed
