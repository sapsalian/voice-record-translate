from dataclasses import dataclass
from pathlib import Path

from soniox.client import SonioxClient
from soniox.types import CreateTranscriptionConfig, Token

TRANSCRIPTION_TIMEOUT = 600  # seconds


@dataclass
class Segment:
    start: float
    end: float
    text: str
    speaker: str | None = None


def transcribe(
    file_path: str,
    api_key: str,
    language: str | None = None,
) -> list[Segment]:
    client = SonioxClient(api_key=api_key)
    with open(file_path, "rb") as f:
        transcription = client.stt.transcribe(
            file=f,
            filename=Path(file_path).name,
            config=CreateTranscriptionConfig(
                language_hints=[language] if language else None,
                enable_speaker_diarization=True,
            ),
        )
    client.stt.wait(transcription.id, timeout_sec=TRANSCRIPTION_TIMEOUT)
    transcript = client.stt.get_transcript(transcription.id)
    return _tokens_to_segments(transcript.tokens)


def _tokens_to_segments(tokens: list[Token]) -> list[Segment]:
    if not tokens:
        return []

    segments: list[Segment] = []
    group: list[Token] = []
    current_speaker: str | None = None

    for token in tokens:
        if not token.text.strip():
            continue
        if group and token.speaker != current_speaker:
            segments.append(_group_to_segment(group, current_speaker))
            group = []
        group.append(token)
        current_speaker = token.speaker

    if group:
        segments.append(_group_to_segment(group, current_speaker))

    return segments


def _group_to_segment(tokens: list[Token], speaker: str | None) -> Segment:
    start = tokens[0].start_ms / 1000.0 if tokens[0].start_ms is not None else 0.0
    end = tokens[-1].end_ms / 1000.0 if tokens[-1].end_ms is not None else start
    text = " ".join(t.text.strip() for t in tokens if t.text.strip())
    return Segment(start=start, end=end, text=text, speaker=speaker)
