from dataclasses import dataclass
from openai import OpenAI


@dataclass
class Segment:
    start: float
    end: float
    text: str


def transcribe(
    file_path: str,
    api_key: str,
    language: str | None = None,
) -> list[Segment]:

    client = OpenAI(api_key=api_key)

    try:
        with open(file_path, "rb") as f:
            params = {
                "model": "gpt-4o-transcribe",
                "file": f,
                "response_format": "verbose_json",
                "timestamp_granularities": ["segment"],
            }

            if language:
                params["language"] = language

            response = client.audio.transcriptions.create(**params)

        segments = getattr(response, "segments", None)
        if not segments:
            return []

        return [
            Segment(
                start=seg.start,
                end=seg.end,
                text=seg.text.strip(),
            )
            for seg in segments
        ]

    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}")
