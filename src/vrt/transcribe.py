import math
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

import av
from openai import OpenAI

MAX_FILE_SIZE = 8 * 1024 * 1024  # 24 MB (Whisper 제한 25MB에서 1MB 여유)
OVERLAP_SECS = 0.5  # 청크 경계 겹침 (단어 잘림 방지)


@dataclass
class Segment:
    start: float
    end: float
    text: str
    no_speech_prob: float | None = None
    avg_logprob: float | None = None


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

        return _dedupe_segments(all_segments)

    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}")


def _normalize_words(text: str) -> list[str]:
    return re.sub(r"[^\w\s]", "", text.lower()).split()


def _merge_texts(a: str, b: str) -> str:
    """A의 접미사와 B의 접두사 중 최장 겹침을 KMP로 찾아 병합."""
    if not a:
        return b
    if not b:
        return a

    wa, wb = a.split(), b.split()
    na, nb = _normalize_words(a), _normalize_words(b)

    s = nb + [None] + na
    pi = [0] * len(s)
    for i in range(1, len(s)):
        j = pi[i - 1]
        while j > 0 and s[i] != s[j]:
            j = pi[j - 1]
        if s[i] == s[j]:
            j += 1
        pi[i] = j

    k = pi[-1]
    return " ".join(wa + wb[k:])


def _dedupe_segments(segments: list[Segment]) -> list[Segment]:
    result = []
    for seg in sorted(segments, key=lambda s: s.start):
        if result and seg.start < result[-1].end:
            prev = result[-1]
            result[-1] = Segment(
                prev.start,
                max(prev.end, seg.end),
                _merge_texts(prev.text, seg.text),
            )
        else:
            result.append(seg)
    return result


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
    return [
        Segment(
            start=s.start,
            end=s.end,
            text=s.text.strip(),
            no_speech_prob=getattr(s, "no_speech_prob", None),
            avg_logprob=getattr(s, "avg_logprob", None),
        )
        for s in segments
    ]


def _split_audio(file_path: str) -> list[tuple[str, float]]:
    """파일이 MAX_FILE_SIZE 이하면 [(file_path, 0.0)] 반환.
    초과 시 PyAV로 N개 청크 분할 후 임시 파일 생성.
    반환: [(chunk_path, offset_seconds), ...]
    """
    file_size = os.path.getsize(file_path)
    if file_size <= MAX_FILE_SIZE:
        return [(file_path, 0.0)]

    with av.open(file_path) as container:
        audio0 = container.streams.audio[0]
        if container.duration is not None:
            duration_secs = container.duration / 1_000_000  # AV_TIME_BASE = μs
        elif audio0.duration is not None:
            duration_secs = float(audio0.duration * audio0.time_base)
        else:
            raise RuntimeError("Cannot determine audio duration")

    n_chunks = math.ceil(file_size / MAX_FILE_SIZE)
    chunk_duration = duration_secs / n_chunks

    chunks = []
    for i in range(n_chunks):
        start = i * chunk_duration
        end = min((i + 1) * chunk_duration + OVERLAP_SECS, duration_secs)

        tmp = tempfile.NamedTemporaryFile(suffix=".m4a", delete=False)
        tmp.close()

        with av.open(file_path) as inp:
            audio = inp.streams.audio[0]
            rate = audio.codec_context.sample_rate or getattr(audio, "rate", 44100)
            channels = audio.codec_context.channels or 1
            layout_str = "mono" if channels == 1 else "stereo" if channels == 2 else f"{channels}c"
            inp.seek(int(start * 1_000_000), any_frame=True, backward=True)

            with av.open(tmp.name, "w", format="mp4") as out:
                out_stream = out.add_stream("aac", rate=rate)
                out_stream.bit_rate = audio.codec_context.bit_rate or 64_000
                resampler = av.AudioResampler(
                    format="fltp",
                    layout=layout_str,
                    rate=rate,
                )

                for frame in inp.decode(audio):
                    if frame.pts is None:
                        continue
                    pts_secs = float(frame.pts * frame.time_base)
                    if pts_secs < start:
                        continue
                    if pts_secs >= end:
                        break
                    frame.pts = None
                    for out_frame in resampler.resample(frame):
                        for pkt in out_stream.encode(out_frame):
                            out.mux(pkt)

                try:
                    for out_frame in resampler.resample(None):
                        for pkt in out_stream.encode(out_frame):
                            out.mux(pkt)
                except Exception:
                    pass
                for pkt in out_stream.encode(None):
                    out.mux(pkt)

        chunks.append((tmp.name, start))

    return chunks
