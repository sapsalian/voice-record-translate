import math
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

import av
from openai import OpenAI

MAX_FILE_SIZE = 24 * 1024 * 1024  # 24 MB (Whisper 제한 25MB에서 1MB 여유)


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
        chunks = _split_audio(file_path)
        all_segments: list[Segment] = []
        temp_paths = [p for p, _ in chunks if p != file_path]

        try:
            for chunk_path, offset in chunks:
                segs = _transcribe_single(chunk_path, client, language)
                all_segments.extend(
                    Segment(start=s.start + offset, end=s.end + offset, text=s.text)
                    for s in segs
                )
        finally:
            for p in temp_paths:
                Path(p).unlink(missing_ok=True)

        return all_segments

    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}")


def _transcribe_single(
    file_path: str,
    client: OpenAI,
    language: str | None,
) -> list[Segment]:
    with open(file_path, "rb") as f:
        params: dict = {
            "model": "whisper-1",
            "file": f,
            "response_format": "verbose_json",
            "timestamp_granularities": ["segment"],
        }
        if language:
            params["language"] = language
        response = client.audio.transcriptions.create(**params)

    segments = getattr(response, "segments", None) or []
    return [Segment(start=s.start, end=s.end, text=s.text.strip()) for s in segments]


def _split_audio(file_path: str) -> list[tuple[str, float]]:
    """파일이 MAX_FILE_SIZE 이하면 [(file_path, 0.0)] 반환.
    초과 시 PyAV로 N개 청크 분할 후 임시 파일 생성.
    반환: [(chunk_path, offset_seconds), ...]
    """
    file_size = os.path.getsize(file_path)
    if file_size <= MAX_FILE_SIZE:
        return [(file_path, 0.0)]

    with av.open(file_path) as container:
        duration_secs = container.duration / 1_000_000  # AV_TIME_BASE = μs

    n_chunks = math.ceil(file_size / MAX_FILE_SIZE)
    chunk_duration = duration_secs / n_chunks

    chunks = []
    for i in range(n_chunks):
        start = i * chunk_duration
        end = min((i + 1) * chunk_duration, duration_secs)

        tmp = tempfile.NamedTemporaryFile(suffix=".m4a", delete=False)
        tmp.close()

        with av.open(file_path) as inp:
            audio = inp.streams.audio[0]
            inp.seek(int(start * 1_000_000))  # AV_TIME_BASE (μs) 단위로 seek

            with av.open(tmp.name, "w", format="mp4") as out:
                out_stream = out.add_stream(template=audio)
                start_pts: int | None = None

                for packet in inp.demux(audio):
                    if packet.pts is None:
                        continue
                    pts_secs = float(packet.pts * packet.time_base)
                    if pts_secs >= end:
                        break
                    # 청크 시작을 pts=0으로 재조정 (Whisper가 0부터 타임스탬프 반환)
                    if start_pts is None:
                        start_pts = packet.pts
                    packet.pts -= start_pts
                    if packet.dts is not None:
                        packet.dts -= start_pts
                    packet.stream = out_stream
                    out.mux(packet)

        chunks.append((tmp.name, start))

    return chunks
