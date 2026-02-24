from dataclasses import dataclass
from typing import Annotated, List

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


@dataclass
class TranslatedSegment:
    start: float
    end: float
    original: str
    translated: str


class TranslationItem(BaseModel):
    index: Annotated[int, Field(ge=1)]
    translated: Annotated[str, Field(min_length=1)]


class TranslationResult(BaseModel):
    items: List[TranslationItem] = Field(default_factory=list)


def translate(
    segments: List[Segment],
    source_lang: str,
    target_lang: str,
    api_key: str,
    model: str = "gpt-4.1",
    temperature: float = 0.3,
) -> List[TranslatedSegment]:
    if not segments:
        return []

    # 1차 시도: 전체 세그먼트
    items = _call_api(segments, source_lang, target_lang, api_key, model, temperature)
    collected = _collect(items, len(segments))

    missing = [i for i in range(1, len(segments) + 1) if i not in collected]

    # 2차 시도: 누락된 세그먼트만 재전송
    if missing:
        missing_segments = [segments[i - 1] for i in missing]
        retry_items = _call_api(missing_segments, source_lang, target_lang, api_key, model, temperature)
        retry_collected = _collect(retry_items, len(missing_segments))

        for pos, orig_idx in enumerate(missing, 1):
            if pos in retry_collected:
                collected[orig_idx] = retry_collected[pos]

        still_missing = [i for i in missing if i not in collected]
        if still_missing:
            raise ValueError(f"번역 실패한 세그먼트 인덱스: {still_missing}")

    return [
        TranslatedSegment(
            start=seg.start,
            end=seg.end,
            original=seg.text,
            translated=collected[i + 1],
        )
        for i, seg in enumerate(segments)
    ]


def _call_api(
    segments: List[Segment],
    source_lang: str,
    target_lang: str,
    api_key: str,
    model: str,
    temperature: float,
) -> List[TranslationItem]:
    source_name = LANGUAGES.get(source_lang, source_lang)
    target_name = LANGUAGES.get(target_lang, target_lang)
    expected_n = len(segments)

    numbered_text = "\n".join(f"{i}: {seg.text}" for i, seg in enumerate(segments, 1))

    system_prompt = (
        "You are a professional translator.\n"
        f"Translate from {source_name} to {target_name}.\n"
        "You MUST return JSON that matches the provided schema.\n"
        "Rules:\n"
        f"- Return exactly {expected_n} items.\n"
        "- Each item must contain:\n"
        "  - index: the original 1-based line number\n"
        "  - translated: the translation of that line only\n"
        "- Do not merge lines. Do not split lines.\n"
        "- Do not add commentary. Do not add extra keys.\n"
        "- Keep meaning faithful and natural in the target language.\n"
    )

    client = OpenAI(api_key=api_key)
    resp = client.responses.parse(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": numbered_text},
        ],
        text_format=TranslationResult,
        temperature=temperature,
    )
    parsed: TranslationResult = resp.output_parsed  # type: ignore[attr-defined]
    if parsed is None:
        return []
    return parsed.items


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
