from pathlib import Path

import pytest

from vrt.srt import _format_timestamp, write_srt


def test_format_timestamp_zero():
    assert _format_timestamp(0.0) == "00:00:00,000"


def test_format_timestamp_basic():
    assert _format_timestamp(1.5) == "00:00:01,500"


def test_format_timestamp_minutes():
    assert _format_timestamp(90.25) == "00:01:30,250"


def test_format_timestamp_hours():
    assert _format_timestamp(3661.001) == "01:01:01,001"


def test_write_srt_content(tmp_path):
    entries = [
        (1.5, 4.2, "Xin chào."),
        (4.5, 7.8, "Tôi là Minh."),
    ]
    out = tmp_path / "test.srt"
    write_srt(entries, str(out))

    content = out.read_text(encoding="utf-8")
    lines = content.split("\n")

    assert lines[0] == "1"
    assert lines[1] == "00:00:01,500 --> 00:00:04,200"
    assert lines[2] == "Xin chào."
    assert lines[3] == ""
    assert lines[4] == "2"
    assert lines[5] == "00:00:04,500 --> 00:00:07,800"
    assert lines[6] == "Tôi là Minh."


def test_write_srt_creates_file(tmp_path):
    out = tmp_path / "out.srt"
    write_srt([(0.0, 1.0, "Hello")], str(out))
    assert out.exists()


def test_write_srt_empty(tmp_path):
    out = tmp_path / "empty.srt"
    write_srt([], str(out))
    assert out.read_text(encoding="utf-8") == ""
