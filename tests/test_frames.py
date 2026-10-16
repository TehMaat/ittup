# -*- coding: utf-8 -*-
import json
import subprocess

import pytest

from ittup.common import config_settings, frames
from ittup.common.frames import VideoFrame, vulkan_device_type, LIBPLACEBO_FILTER, TONEMAP_FILTER
from ittup.common.settings import Load, UserPreferences

# ffmpeg 8.1 verbose log of the libplacebo test frame
GPU_LOG = """\
[libplacebo @ 0x557dcd1f2280] Probing for vulkan devices:
[libplacebo @ 0x557dcd1f2280]     GPU 0: NVIDIA GeForce RTX 4070 Ti SUPER v1.4.351 (discrete)
[libplacebo @ 0x557dcd1f2280]     GPU 1: llvmpipe (LLVM 22.1.8, 256 bits) v1.4.354 (software)
[libplacebo @ 0x557dcd1f2280] Vulkan device properties:
[libplacebo @ 0x557dcd1f2280]     Device Name: NVIDIA GeForce RTX 4070 Ti SUPER
[libplacebo @ 0x557dcd1f2280]     Device ID: 10de:2705
"""

SOFTWARE_LOG = """\
[libplacebo @ 0x555f11814280] Probing for vulkan devices:
[libplacebo @ 0x555f11814280]     GPU 0: llvmpipe (LLVM 22.1.8, 256 bits) v1.4.354 (software)
[libplacebo @ 0x555f11814280] Vulkan device properties:
[libplacebo @ 0x555f11814280]     Device Name: llvmpipe (LLVM 22.1.8, 256 bits)
"""


def test_device_type_of_the_chosen_gpu():
    assert vulkan_device_type(GPU_LOG) == "discrete"


def test_device_type_software():
    assert vulkan_device_type(SOFTWARE_LOG) == "software"


def test_device_type_not_logged():
    assert vulkan_device_type("[libplacebo @ 0x1] GPU information:\n") == "unknown"


def video_filter(monkeypatch, color_transfer, dv_profile=None, device_type="discrete", can_tonemap=True,
                 tonemap=True):
    """
    Filter chosen for a video with this ffprobe output, libplacebo device and zscale support
    """
    monkeypatch.setattr(config_settings.user_preferences, "TONEMAP_SCSHOT", tonemap)
    stream = {"color_transfer": color_transfer}
    if dv_profile is not None:
        stream["side_data_list"] = [{"dv_profile": dv_profile}]
    probe = json.dumps({"streams": [stream]})
    monkeypatch.setattr(frames.subprocess, "run",
                        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, stdout=probe))
    monkeypatch.setattr(frames, "libplacebo_device_type", lambda: device_type)
    monkeypatch.setattr(frames, "ffmpeg_can_tonemap", lambda: can_tonemap)
    return VideoFrame("video.mkv", 4)._get_video_filter()


def test_sdr_video_is_not_tone_mapped(monkeypatch):
    assert video_filter(monkeypatch, "bt709") == []


@pytest.mark.parametrize("color_transfer, dv_profile", [("smpte2084", None), ("unknown", 5)])
def test_tone_mapping_disabled(monkeypatch, color_transfer, dv_profile):
    assert video_filter(monkeypatch, color_transfer, dv_profile=dv_profile, tonemap=False) == []


def test_tone_mapping_is_off_by_default():
    assert UserPreferences.model_fields["TONEMAP_SCSHOT"].default is False
    assert Load.default_config()["user_preferences"]["TONEMAP_SCSHOT"] == "False"


@pytest.mark.parametrize("device_type", ["discrete", "integrated", "unknown"])
def test_libplacebo_on_a_gpu(monkeypatch, device_type):
    assert video_filter(monkeypatch, "smpte2084", device_type=device_type) == ["-vf", LIBPLACEBO_FILTER]


def test_zscale_instead_of_software_vulkan(monkeypatch):
    assert video_filter(monkeypatch, "smpte2084", dv_profile=8, device_type="software") == ["-vf", TONEMAP_FILTER]


def test_software_vulkan_for_dolby_vision_profile_5(monkeypatch):
    assert video_filter(monkeypatch, "unknown", dv_profile=5, device_type="software") == ["-vf", LIBPLACEBO_FILTER]


def test_software_vulkan_without_zscale(monkeypatch):
    assert video_filter(monkeypatch, "smpte2084", device_type="software",
                        can_tonemap=False) == ["-vf", LIBPLACEBO_FILTER]


def test_zscale_without_libplacebo(monkeypatch):
    assert video_filter(monkeypatch, "smpte2084", device_type=None) == ["-vf", TONEMAP_FILTER]


@pytest.mark.parametrize("value, timeout", [(120, 120), (45, 45), (0, None)])
def test_screenshot_timeout(monkeypatch, value, timeout):
    monkeypatch.setattr(config_settings.user_preferences, "TIMEOUT_SCSHOT", value)
    assert VideoFrame("video.mkv", 4).timeout == timeout
