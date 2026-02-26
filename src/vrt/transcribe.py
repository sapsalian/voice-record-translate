import tempfile
from dataclasses import dataclass
from pathlib import Path

import av
from soniox.client import SonioxClient
from soniox.types import CreateTranscriptionConfig, Token

TRANSCRIPTION_TIMEOUT = 600  # seconds
MAX_DURATION_SEC = 18_000    # 300 minutes — Soniox hard limit
CHUNK_MAX_SEC = 9_000        # 150 minutes — split threshold


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
    duration = _get_duration(file_path)
    if duration is not None and duration > MAX_DURATION_SEC:
        minutes = int(duration / 60)
        raise ValueError(
            f"파일 재생 시간이 {minutes}분으로 Soniox 최대 허용 시간(300분)을 초과합니다."
        )
    if duration is None or duration <= CHUNK_MAX_SEC:
        return _transcribe_file(file_path, api_key)
    return _transcribe_chunked(file_path, api_key)


def _get_duration(file_path: str) -> float | None:
    with av.open(file_path) as container:
        if container.duration is None:
            return None
        return container.duration / 1_000_000  # av uses microseconds


def _check_duration(file_path: str) -> None:
    """기존 테스트 호환용. transcribe() 내부에서는 _get_duration() 사용."""
    duration = _get_duration(file_path)
    if duration is not None and duration > MAX_DURATION_SEC:
        minutes = int(duration / 60)
        raise ValueError(
            f"파일 재생 시간이 {minutes}분으로 Soniox 최대 허용 시간(300분)을 초과합니다."
        )


def _transcribe_file(file_path: str, api_key: str, offset: float = 0.0) -> list[Segment]:
    """단일 파일 전사. offset(초)만큼 모든 타임스탬프를 이동."""
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
    segs = _tokens_to_segments(transcript.tokens)
    if offset:
        segs = [Segment(s.start + offset, s.end + offset, s.text, s.speaker) for s in segs]
    return segs


def _transcribe_chunked(file_path: str, api_key: str) -> list[Segment]:
    """150분 단위 분할 전사 + 화자 ID 재매핑."""
    all_segments: list[Segment] = []
    next_speaker_id = 1

    with tempfile.TemporaryDirectory() as tmp_dir:
        for chunk_path, offset in _split_audio(file_path, CHUNK_MAX_SEC, Path(tmp_dir)):
            segs = _transcribe_file(chunk_path, api_key, offset=offset)

            # 이 청크의 화자 ID를 이전 청크와 겹치지 않는 새 ID로 재매핑
            speaker_map: dict[str, str] = {}
            for seg in segs:
                if seg.speaker is not None and seg.speaker not in speaker_map:
                    speaker_map[seg.speaker] = str(next_speaker_id)
                    next_speaker_id += 1

            all_segments.extend(
                Segment(
                    start=seg.start,
                    end=seg.end,
                    text=seg.text,
                    speaker=speaker_map.get(seg.speaker) if seg.speaker else None,
                )
                for seg in segs
            )

    return all_segments


def _split_audio(file_path: str, chunk_sec: float, tmp_dir: Path) -> list[tuple[str, float]]:
    """PyAV로 오디오를 chunk_sec 단위로 분할. [(tmp_path, offset_sec)] 반환.

    재인코딩 없이 패킷 복사. 각 청크 타임스탬프는 0부터 시작하도록 재계산.
    """
    results: list[tuple[str, float]] = []

    with av.open(file_path) as src:
        audio = src.streams.audio[0]
        total_sec = (src.duration / 1_000_000) if src.duration else 0.0

        start_sec = 0.0
        chunk_idx = 0
        while start_sec < total_sec:
            end_sec = min(start_sec + chunk_sec, total_sec)
            out_path = tmp_dir / f"chunk_{chunk_idx}{Path(file_path).suffix}"

            src.seek(int(start_sec * 1_000_000))

            with av.open(str(out_path), "w") as dst:
                dst_audio = dst.add_stream(template=audio)
                for packet in src.demux(audio):
                    if packet.pts is None:
                        continue
                    pts_sec = float(packet.pts * audio.time_base)
                    if pts_sec >= end_sec:
                        break
                    if pts_sec >= start_sec:
                        offset_pts = int(start_sec / float(audio.time_base))
                        packet.pts -= offset_pts
                        if packet.dts is not None:
                            packet.dts -= offset_pts
                        packet.stream = dst_audio
                        dst.mux(packet)

            results.append((str(out_path), start_sec))
            start_sec = end_sec
            chunk_idx += 1

    return results


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
