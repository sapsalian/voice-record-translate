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
        response_format=TranslationResult,
        temperature=temperature,
    )
    parsed: TranslationResult = resp.output_parsed  # type: ignore[attr-defined]
    if parsed is None:
        raise ValueError("No structured output returned from translation.")
    translated_lines = _validate_and_normalize(parsed.items, expected_n)

    return [
        TranslatedSegment(
            start=seg.start,
            end=seg.end,
            original=seg.text,
            translated=translated_lines[i],
        )
        for i, seg in enumerate(segments)
    ]


def _validate_and_normalize(items: List[TranslationItem], expected_n: int) -> List[str]:
    if len(items) != expected_n:
        raise ValueError(f"Translation returned {len(items)} items, expected {expected_n}")

    out = [""] * expected_n
    seen: set[int] = set()

    for it in items:
        idx = int(it.index)
        if idx < 1 or idx > expected_n:
            raise ValueError(f"Invalid index {idx}; expected 1..{expected_n}")
        if idx in seen:
            raise ValueError(f"Duplicate index {idx} in translation output")
        seen.add(idx)

        text = it.translated.strip()
        if not text:
            raise ValueError(f"Empty translation at index {idx}")
        out[idx - 1] = text

    for i, v in enumerate(out, 1):
        if not v:
            raise ValueError(f"Missing translation for index {i}")

    return out
