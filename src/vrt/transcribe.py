from dataclasses import dataclass
from pathlib import Path

import av
from soniox.client import SonioxClient
from soniox.types import CreateTranscriptionConfig, Token

TRANSCRIPTION_TIMEOUT = 600  # seconds
MAX_DURATION_SEC = 18_000    # 300 minutes — Soniox hard limit


@dataclass
class Segment:
    start: float
    end: float
    text: str
    speaker: str | None = None


def transcribe(
    file_path: str,
    api_key: str,
) -> list[Segment]:
    _check_duration(file_path)
    client = SonioxClient(api_key=api_key)
    with open(file_path, "rb") as f:
        transcript = client.stt.transcribe_and_wait_with_tokens(
            file=f,
            filename=Path(file_path).name,
            config=CreateTranscriptionConfig(
                enable_speaker_diarization=True,
            ),
            delete_after=True,
            wait_timeout_sec=TRANSCRIPTION_TIMEOUT,
        )
    return _tokens_to_segments(transcript.tokens)


def _check_duration(file_path: str) -> None:
    with av.open(file_path) as container:
        if container.duration is None:
            return
        duration_sec = container.duration / 1_000_000  # av uses microseconds
        if duration_sec > MAX_DURATION_SEC:
            minutes = int(duration_sec / 60)
            raise ValueError(
                f"파일 재생 시간이 {minutes}분으로 Soniox 최대 허용 시간(300분)을 초과합니다."
            )


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
