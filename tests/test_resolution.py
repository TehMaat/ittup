# -*- coding: utf-8 -*-
import pytest

from ittup.core.media import Media


@pytest.mark.parametrize("width, height, resolution", [
    (3840, 2160, "2160p"),
    (3840, 1600, "2160p"),
    (2880, 2160, "2160p"),
    (1920, 1080, "1080p"),
    (1920, 800, "1080p"),
    (1440, 1080, "1080p"),
    (1080, 1080, "1080p"),
    (1280, 720, "720p"),
    (1280, 536, "720p"),
    (960, 720, "720p"),
    (1024, 576, "576p"),
    (720, 576, "576p"),
    (720, 480, "480p"),
    (736, 414, "480p"),
    (720, 404, "480p"),
    (640, 360, "480p"),
    (480, 270, "480p"),
])
def test_the_resolution_is_the_highest_one_reached_by_the_width_or_the_height(width, height, resolution):
    assert Media.resolution_from_size(width, height) == resolution


def test_without_the_height_the_width_is_used():
    assert Media.resolution_from_size(1920, None) == "1080p"
    assert Media.resolution_from_size(736, None) == "480p"


@pytest.mark.parametrize("width, height, resolution", [
    (1920, 1080, "1080i"),
    (1440, 1080, "1080i"),
    (720, 576, "576i"),
    (720, 480, "480i"),
    (736, 414, "480i"),
    (1280, 720, "720p"),
    (3840, 2160, "2160p"),
])
def test_an_interlaced_video_has_an_interlaced_resolution_when_the_tracker_has_one(width, height, resolution):
    assert Media.resolution_from_size(width, height, interlaced=True) == resolution


class MediaFile:
    def __init__(self, scan_type):
        self.video_width, self.video_height, self.video_scan_type = 1920, 1080, scan_type


@pytest.mark.parametrize("scan_type, resolution", [
    ("Interlaced", "1080i"),
    ("MBAFF", "1080i"),
    ("PAFF", "1080i"),
    ("Progressive", "1080p"),
    ("Mixed", "1080p"),
    (None, "1080p"),
])
def test_the_scan_type_of_mediainfo_decides_if_the_video_is_interlaced(monkeypatch, scan_type, resolution):
    media = Media.__new__(Media)
    monkeypatch.setattr(Media, "mediafile", MediaFile(scan_type))

    assert media._resolution2 == resolution
