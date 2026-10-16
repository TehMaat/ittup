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
    (640, 360, "360p"),
])
def test_the_resolution_is_the_highest_one_reached_by_the_width_or_the_height(width, height, resolution):
    assert Media.resolution_from_size(width, height) == resolution


def test_without_the_height_the_width_is_used():
    assert Media.resolution_from_size(1920, None) == "1080p"
