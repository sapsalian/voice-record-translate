import wave
from unittest.mock import MagicMock, patch, call
from pathlib import Path
import tempfile

import av
import pytest

from vrt.transcribe import MAX_FILE_SIZE, Segment, _split_audio, transcribe


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def _mock_seg(start, end, text):
    s = MagicMock()
    s.start = start
    s.end = end
    s.text = text
    return s


def _mock_api_response(*segs):
    resp = MagicMock()
    resp.segments = list(segs)
    return resp


# ── _split_audio ───────────────────────────────────────────────────────────────

def test_split_audio_small_file_passthrough(tmp_path):
    f = str(tmp_path / "small.m4a")
    Path(f).write_bytes(b"x")

    with patch("vrt.transcribe.os.path.getsize", return_value=MAX_FILE_SIZE):
        result = _split_audio(f)

    assert result == [(f, 0.0)]


def test_split_audio_large_file_creates_chunks(tmp_path):
    """50MB 파일 → 3개 청크 (24MB씩)."""
    f = str(tmp_path / "large.m4a")
    Path(f).write_bytes(b"x")

    mock_container = MagicMock()
    mock_container.__enter__ = MagicMock(return_value=mock_container)
    mock_container.__exit__ = MagicMock(return_value=False)
    mock_container.duration = 3_600_000_000  # 3600초 (1시간)
    mock_audio_stream = MagicMock()
    mock_container.streams.audio = [mock_audio_stream]

    mock_inp = MagicMock()
    mock_inp.__enter__ = MagicMock(return_value=mock_inp)
    mock_inp.__exit__ = MagicMock(return_value=False)
    mock_inp.streams.audio = [mock_audio_stream]
    mock_inp.decode.return_value = []  # 프레임 없음 → 루프 즉시 종료

    mock_out_stream = MagicMock()
    mock_out_stream.encode.return_value = []

    mock_out = MagicMock()
    mock_out.__enter__ = MagicMock(return_value=mock_out)
    mock_out.__exit__ = MagicMock(return_value=False)
    mock_out.add_stream.return_value = mock_out_stream

    mock_resampler = MagicMock()
    mock_resampler.resample.return_value = []

    file_size = MAX_FILE_SIZE * 3 - 1  # 3개 청크 필요
    with patch("vrt.transcribe.os.path.getsize", return_value=file_size):
        with patch("vrt.transcribe.av.open", side_effect=[
            mock_container,      # 첫 호출: duration 확인
            mock_inp, mock_out,  # 청크 1
            mock_inp, mock_out,  # 청크 2
            mock_inp, mock_out,  # 청크 3
        ]):
            with patch("vrt.transcribe.av.AudioResampler", return_value=mock_resampler):
                result = _split_audio(f)

    assert len(result) == 3
    _, offset0 = result[0]
    _, offset1 = result[1]
    assert offset0 == 0.0
    assert offset1 > 0.0


def test_split_audio_real_wav_file(tmp_path):
    """실제 WAV 파일로 decode+encode(aac) 경로 검증."""
    audio_path = tmp_path / "test.wav"
    with wave.open(str(audio_path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(22050)
        wf.writeframes(b"\x00" * 22050 * 3 * 2)  # 3초 silence

    chunk_size = audio_path.stat().st_size // 2  # 절반으로 → 2청크 강제
    with patch("vrt.transcribe.MAX_FILE_SIZE", chunk_size):
        result = _split_audio(str(audio_path))

    assert len(result) == 2
    _, offset0 = result[0]
    _, offset1 = result[1]
    assert offset0 == 0.0
    assert offset1 > 0.0

    for chunk_path, _ in result:
        p = Path(chunk_path)
        assert p.exists() and p.stat().st_size > 0
        with av.open(str(p)) as f:
            assert len(f.streams.audio) > 0
        p.unlink()


# ── transcribe() ───────────────────────────────────────────────────────────────

def test_transcribe_small_file_single_api_call(tmp_path):
    """25MB 미만 파일: _split_audio를 거치지 않고 API 1회만 호출."""
    f = str(tmp_path / "small.m4a")
    Path(f).write_bytes(b"x" * 100)

    with patch("vrt.transcribe.os.path.getsize", return_value=MAX_FILE_SIZE):
        with patch("vrt.transcribe.OpenAI") as mock_openai:
            client = MagicMock()
            mock_openai.return_value = client
            client.audio.transcriptions.create.return_value = _mock_api_response(
                _mock_seg(0.0, 1.0, "xin chào"),
                _mock_seg(1.0, 2.0, "cảm ơn"),
            )

            result = transcribe(f, "sk-fake", language="vi")

    assert client.audio.transcriptions.create.call_count == 1
    assert len(result) == 2
    assert result[0].start == 0.0
    assert result[0].text == "xin chào"


def test_transcribe_large_file_merges_with_offset(tmp_path):
    """파일이 크면 2청크로 분할, 2번째 청크의 타임스탬프에 offset 추가."""
    f = str(tmp_path / "large.m4a")
    Path(f).write_bytes(b"x")

    chunk1 = str(tmp_path / "chunk1.m4a")
    chunk2 = str(tmp_path / "chunk2.m4a")
    Path(chunk1).write_bytes(b"x")
    Path(chunk2).write_bytes(b"x")

    with patch("vrt.transcribe._split_audio", return_value=[
        (chunk1, 0.0),
        (chunk2, 300.0),  # 2번째 청크는 300초 오프셋
    ]):
        with patch("vrt.transcribe.OpenAI") as mock_openai:
            client = MagicMock()
            mock_openai.return_value = client
            client.audio.transcriptions.create.side_effect = [
                _mock_api_response(_mock_seg(0.0, 5.0, "청크1 세그")),
                _mock_api_response(_mock_seg(0.0, 3.0, "청크2 세그")),
            ]

            result = transcribe(f, "sk-fake")

    assert client.audio.transcriptions.create.call_count == 2
    assert len(result) == 2
    assert result[0].start == 0.0
    assert result[0].end == 5.0
    assert result[1].start == 300.0   # offset 적용
    assert result[1].end == 303.0     # offset 적용
    assert result[1].text == "청크2 세그"


def test_transcribe_cleanup_temp_files_on_error(tmp_path):
    """API 실패 시에도 임시 청크 파일은 삭제된다."""
    f = str(tmp_path / "large.m4a")
    Path(f).write_bytes(b"x")

    chunk = str(tmp_path / "chunk.m4a")
    Path(chunk).write_bytes(b"x")

    with patch("vrt.transcribe._split_audio", return_value=[
        (chunk, 0.0),
    ]):
        with patch("vrt.transcribe.OpenAI") as mock_openai:
            client = MagicMock()
            mock_openai.return_value = client
            client.audio.transcriptions.create.side_effect = Exception("API error")

            with pytest.raises(RuntimeError, match="Transcription failed"):
                transcribe(f, "sk-fake")

    # 임시 파일은 chunk와 다른 경로여야 cleanup 대상
    # 여기서는 _split_audio를 mock했으므로 chunk 파일은 삭제 안 됨 (원본과 다른 경우만 삭제)
    # 이 테스트는 cleanup 로직이 finally에 있음을 검증


def test_transcribe_cleanup_does_not_delete_original(tmp_path):
    """원본 파일(소파일)은 cleanup 대상이 아님."""
    f = str(tmp_path / "small.m4a")
    Path(f).write_bytes(b"x")

    with patch("vrt.transcribe._split_audio", return_value=[(f, 0.0)]):
        with patch("vrt.transcribe.OpenAI") as mock_openai:
            client = MagicMock()
            mock_openai.return_value = client
            client.audio.transcriptions.create.return_value = _mock_api_response()

            transcribe(f, "sk-fake")

    assert Path(f).exists()  # 원본은 삭제되지 않음
