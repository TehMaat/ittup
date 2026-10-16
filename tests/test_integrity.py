# -*- coding: utf-8 -*-
import json

import pytest

from ittup.common.integrity import MediaIntegrity

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
