from dataclasses import dataclass
from typing import Annotated, Callable, List

from openai import OpenAI
from pydantic import BaseModel, Field

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


@dataclass
class _ChunkCtx:
    summary: str
    recent_pairs: list[tuple[str, str]]  # (원문, 번역) 최근 CONTEXT_PAIRS쌍


class TranslationItem(BaseModel):
    index: Annotated[int, Field(ge=1)]
    translated: Annotated[str, Field(min_length=1)]


class ChunkResult(BaseModel):
    items: List[TranslationItem]
    summary: str


def translate(
    segments: List[Segment],
    source_lang: str,
    target_lang: str,
    api_key: str,
    model: str = "gpt-4.1",
    temperature: float = 0.3,
    progress_callback: Callable[[int, int], None] | None = None,
) -> List[TranslatedSegment]:
    if not segments:
        return []

    chunks = [segments[i:i + CHUNK_SIZE] for i in range(0, len(segments), CHUNK_SIZE)]
    total_chunks = len(chunks)
    all_collected: dict[int, str] = {}  # global 1-based index → translated
    ctx: _ChunkCtx | None = None

    for chunk_idx, chunk in enumerate(chunks):
        global_offset = chunk_idx * CHUNK_SIZE  # 이 청크의 첫 세그먼트의 global index (0-based)

        collected, ctx = _translate_chunk(chunk, source_lang, target_lang, api_key, model, temperature, ctx)

        for local_idx, text in collected.items():
            all_collected[global_offset + local_idx] = text  # 1-based global key

        if progress_callback:
            progress_callback(chunk_idx + 1, total_chunks)

    return [
        TranslatedSegment(
            start=seg.start,
            end=seg.end,
            original=seg.text,
            translated=all_collected[i + 1],  # 1-based
        )
        for i, seg in enumerate(segments)
    ]


def _translate_chunk(
    chunk: List[Segment],
    source_lang: str,
    target_lang: str,
    api_key: str,
    model: str,
    temperature: float,
    ctx: _ChunkCtx | None,
) -> tuple["_ChunkCtx", dict[int, str]]:
    result = _call_api_chunk(chunk, source_lang, target_lang, api_key, model, temperature, ctx)
    collected = _collect(result.items, len(chunk))

    missing = [i for i in range(1, len(chunk) + 1) if i not in collected]
    if missing:
        missing_segs = [chunk[i - 1] for i in missing]
        retry = _call_api_chunk(missing_segs, source_lang, target_lang, api_key, model, temperature, ctx=None)
        retry_collected = _collect(retry.items, len(missing_segs))
        for pos, orig_idx in enumerate(missing, 1):
            if pos in retry_collected:
                collected[orig_idx] = retry_collected[pos]

        still_missing = [i for i in missing if i not in collected]
        if still_missing:
            raise ValueError(f"번역 실패한 세그먼트 인덱스: {still_missing}")

    # 다음 청크를 위한 컨텍스트 구성
    pairs = [(chunk[i - 1].text, collected[i]) for i in sorted(collected)]
    new_ctx = _ChunkCtx(
        summary=result.summary,
        recent_pairs=pairs[-CONTEXT_PAIRS:],
    )
    return collected, new_ctx


def _call_api_chunk(
    segments: List[Segment],
    source_lang: str,
    target_lang: str,
    api_key: str,
    model: str,
    temperature: float,
    ctx: _ChunkCtx | None,
) -> ChunkResult:
    source_name = LANGUAGES.get(source_lang, source_lang)
    target_name = LANGUAGES.get(target_lang, target_lang)
    expected_n = len(segments)

    numbered_text = "\n".join(f"{i}: {seg.text}" for i, seg in enumerate(segments, 1))

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
        f"[번역 지시]\n"
        f"You are a professional translator.\n"
        f"Translate from {source_name} to {target_name}.\n"
        f"You MUST return JSON that matches the provided schema.\n"
        f"Rules:\n"
        f"- Return exactly {expected_n} items.\n"
        f"- Each item: index (1-based line number), translated (translation of that line only).\n"
        f"- Do not merge or split lines.\n"
        f"- Keep meaning faithful and natural in the target language.\n"
        f"- summary: 이전 누적 요약(있다면)과 이번 청크 내용을 합쳐 전체 대화의 누적 요약을 작성. "
        f"고유명사(이름, 회사명, 지역명)와 주요 주제를 반드시 포함. 2~5문장.\n"
    )

    client = OpenAI(api_key=api_key)
    resp = client.responses.parse(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": numbered_text},
        ],
        text_format=ChunkResult,
        temperature=temperature,
    )
    parsed: ChunkResult = resp.output_parsed  # type: ignore[attr-defined]
    if parsed is None:
        return ChunkResult(items=[], summary="")
    return parsed


def _collect(items: List[TranslationItem], expected_n: int) -> dict[int, str]:
    """유효한 번역 항목만 수집. {1-based index: translated text}"""
    result: dict[int, str] = {}
    for it in items:
        idx = int(it.index)
        if 1 <= idx <= expected_n and idx not in result:
            text = it.translated.strip()
            if text:
                result[idx] = text
    return result
