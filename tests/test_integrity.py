# -*- coding: utf-8 -*-
import json

import pytest

from ittup.common.integrity import MediaIntegrity, UnsupportedFFprobe

DURATION = 1000.0
RPU_ERROR = "[hevc @ 0x55d0c0a1b2c0] RPU validation failed: 0 <= el_bit_depth_minus8 = 32 <= 8"
HEVC_ERROR = "[hevc @ 0x55d0c0a1b2c0] Invalid NAL unit size (1234 > 567)."


def fake_ffprobe(monkeypatch, frames_stderr: str = "", last_frame: float = 900.0, returncode: int = 0):
    """
    ffprobe that reads the duration and decodes frames up to last_frame; records the read intervals
    """
    calls = []

    def ffprobe(arguments):
        if "-read_intervals" in arguments:
            calls.append(arguments[arguments.index("-read_intervals") + 1])
            return returncode, f"100.0,\n500.0,\n{last_frame},\n", frames_stderr
        return 0, json.dumps({"format": {"duration": str(DURATION)}}), ""

    monkeypatch.setattr(MediaIntegrity, "ffprobe", staticmethod(ffprobe))
    monkeypatch.setattr(MediaIntegrity, "ffprobe_version", staticmethod(lambda: ("ffprobe version 8.1.3", (8, 1))))
    return calls


def test_default_range_samples_10_50_90(monkeypatch):
    calls = fake_ffprobe(monkeypatch)
    assert MediaIntegrity.check_file("video.mkv") == (None, None)
    assert calls == ["100.00%+#3,500.00%+#3,900.00%+#3"]


def test_custom_range(monkeypatch):
    calls = fake_ffprobe(monkeypatch, last_frame=800.0)
    assert MediaIntegrity.check_file("video.mkv", start=20, end=80) == (None, None)
    assert calls == ["200.00%+#3,500.00%+#3,800.00%+#3"]


def test_truncated_before_the_end_of_the_range(monkeypatch):
    fake_ffprobe(monkeypatch, last_frame=600.0)
    error, _ = MediaIntegrity.check_file("video.mkv")
    assert error.startswith("truncated")


@pytest.mark.parametrize("ignore", [False, True])
def test_other_errors_always_fail(monkeypatch, ignore):
    fake_ffprobe(monkeypatch, frames_stderr=f"{RPU_ERROR}\n{HEVC_ERROR}")
    error, ignored = MediaIntegrity.check_file("video.mkv", ignore_dolby_vision=ignore)
    assert error == (HEVC_ERROR.split("] ")[1] if ignore else RPU_ERROR.split("] ")[1])
    assert ignored is None


def test_dolby_vision_error_fails_by_default(monkeypatch):
    fake_ffprobe(monkeypatch, frames_stderr=RPU_ERROR)
    assert MediaIntegrity.check_file("video.mkv") == ("RPU validation failed: 0 <= el_bit_depth_minus8 = 32 <= 8",
                                                      None)


def test_dolby_vision_error_ignored(monkeypatch):
    fake_ffprobe(monkeypatch, frames_stderr=RPU_ERROR)
    assert MediaIntegrity.check_file("video.mkv", ignore_dolby_vision=True) == (
        None, "RPU validation failed: 0 <= el_bit_depth_minus8 = 32 <= 8")


def test_check_splits_errors_and_ignored(monkeypatch, tmp_path):
    fake_ffprobe(monkeypatch, frames_stderr=RPU_ERROR)
    video = tmp_path / "video.mkv"
    video.write_bytes(b"")
    errors, ignored = MediaIntegrity.check(str(video), ignore_dolby_vision=True)
    assert errors == {}
    assert list(ignored) == [str(video)]


def fake_ffprobe_version(monkeypatch, line: str):
    class Result:
        stdout = f"{line} Copyright (c) 2007-2026 the FFmpeg developers\nbuilt with gcc 15\n"

    monkeypatch.setattr("ittup.common.integrity.subprocess.run", lambda *args, **kwargs: Result())
    MediaIntegrity.ffprobe_version.cache_clear()


@pytest.mark.parametrize("line, version", [
    ("ffprobe version 4.4.2-0ubuntu0.22.04.1", (4, 4)),
    ("ffprobe version 5.1.9-0+deb12u1", (5, 1)),
    ("ffprobe version n6.1.1", (6, 1)),
    ("ffprobe version N-112345-g0123abcd", None),
])
def test_ffprobe_version(monkeypatch, line, version):
    fake_ffprobe_version(monkeypatch, line)
    assert MediaIntegrity.ffprobe_version() == (line, version)


def test_ffprobe_4_4_is_unsupported(monkeypatch, tmp_path):
    fake_ffprobe_version(monkeypatch, "ffprobe version 4.4.2-0ubuntu0.22.04.1")
    with pytest.raises(UnsupportedFFprobe, match="4.4.2"):
        MediaIntegrity.check(str(tmp_path / "video.mkv"))
