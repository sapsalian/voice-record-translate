"""음성 파일 분할 데모.

Usage:
    python demo_split.py <audio_file> [chunk_mb]

Arguments:
    audio_file  분할할 음성 파일 경로
    chunk_mb    청크 크기 (MB 단위, 기본값: 1)  ← 테스트용으로 작게 설정 가능
"""
import math
import os
import shutil
import sys
from pathlib import Path

import av

DEFAULT_CHUNK_MB = 8  # 데모 기본값: 1MB (실제는 24MB)
OVERLAP_SECS = 0.5


def split_audio(file_path: str, chunk_mb: float) -> list[tuple[str, float, float]]:
    """음성 파일을 chunk_mb 단위로 분할, 결과 경로 목록 반환.

    Returns: [(output_path, start_sec, end_sec), ...]
    """
    max_bytes = int(chunk_mb * 1024 * 1024)
    file_size = os.path.getsize(file_path)

    if file_size <= max_bytes:
        print(f"파일 크기 {file_size / 1024:.1f} KB ≤ {chunk_mb} MB → 분할 불필요")
        return [(file_path, 0.0, None)]

    with av.open(file_path) as container:
        audio0 = container.streams.audio[0]
        if container.duration is not None:
            duration_secs = container.duration / 1_000_000
        elif audio0.duration is not None:
            duration_secs = float(audio0.duration * audio0.time_base)
        else:
            raise RuntimeError("오디오 길이를 확인할 수 없습니다")

    n_chunks = math.ceil(file_size / max_bytes)
    chunk_duration = duration_secs / n_chunks

    src = Path(file_path)
    out_dir = src.parent / f"{src.stem}_chunks"
    out_dir.mkdir(exist_ok=True)

    print(f"파일 크기: {file_size / 1024 / 1024:.2f} MB")
    print(f"총 길이: {duration_secs:.2f}초")
    print(f"청크 크기: {chunk_mb} MB → {n_chunks}개 분할")
    print(f"출력 디렉터리: {out_dir}\n")

    results = []
    for i in range(n_chunks):
        start = i * chunk_duration
        end = min((i + 1) * chunk_duration + OVERLAP_SECS, duration_secs)

        out_path = out_dir / f"{src.stem}_chunk{i:02d}.m4a"

        with av.open(file_path) as inp:
            audio = inp.streams.audio[0]
            rate = audio.codec_context.sample_rate or 44100
            channels = audio.codec_context.channels or 1
            layout = "mono" if channels == 1 else "stereo" if channels == 2 else f"{channels}c"
            inp.seek(int(start * 1_000_000), any_frame=True, backward=True)

            with av.open(str(out_path), "w", format="mp4") as out:
                out_stream = out.add_stream("aac", rate=rate)
                out_stream.bit_rate = audio.codec_context.bit_rate or 64_000
                resampler = av.AudioResampler(format="fltp", layout=layout, rate=rate)

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

        size_kb = out_path.stat().st_size / 1024
        print(f"  chunk{i:02d}: {start:.2f}s ~ {end:.2f}s  ({size_kb:.1f} KB)  → {out_path.name}")
        results.append((str(out_path), start, end))

    print(f"\n완료: {n_chunks}개 파일 저장됨 → {out_dir}")
    return results


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    file_path = sys.argv[1]
    chunk_mb = float(sys.argv[2]) if len(sys.argv) >= 3 else DEFAULT_CHUNK_MB

    if not Path(file_path).exists():
        print(f"파일 없음: {file_path}")
        sys.exit(1)

    split_audio(file_path, chunk_mb)


if __name__ == "__main__":
    main()
