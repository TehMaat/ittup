# -*- coding: utf-8 -*-
from types import SimpleNamespace

import pytest

from ittup.common.tags import SearchTags
from ittup.common.trackers.trackers import TRACKData

POSITION = ["title", "year", "resolution", "source", "remux", "vcodec"]


def search(filename: str, general: dict | None = None, video: dict | None = None) -> SearchTags:
    mediafile = SimpleNamespace(general_track=general or {}, video_track=[{"format": "AVC", **(video or {})}],
                                audio_track=[], subtitle_track=[])
    media = SimpleNamespace(mediafile=mediafile, torrent_pack=False, resolution="1080p", pack=None)
    return SearchTags(filename=filename, title="Movie", year=2020, season=None, episode=None, media=media,
                      tags_position=POSITION, releaser_sign="")


def test_the_source_of_the_name_wins():
    tags = search("Movie.2020.1080p.WEBRip.mkv", general={"title": "Movie.2020.1080p.WEB-DL.H.264-GRP"})
    assert tags.process()[0] == "Movie 2020 WEBRip x264"
    assert tags.mediainfo_tags == {}


@pytest.mark.parametrize("general, video, expected, source", [
    # The release name kept in the metadata title
    ({"title": "Movie.2020.1080p.WEB-DL.H.264-GRP"}, {}, "Movie 2020 WEB-DL H.264", {"source": ["WEB-DL"]}),
    ({"movie_name": "Movie 2020 1080p BluRay x264-GRP"}, {"writing_library": "x264 core 164"},
     "Movie 2020 BluRay x264", {"source": ["BluRay"]}),
    # MakeMKV: the video copied from the Blu-ray is a remux
    ({"original_source_medium": "Blu-ray"}, {}, "Movie 2020 BluRay REMUX AVC",
     {"source": ["BluRay"], "remux": ["REMUX"]}),
    ({}, {"original_source_medium": "Blu-ray", "writing_library": "x264 core 164"}, "Movie 2020 BluRay x264",
     {"source": ["BluRay"]}),
    ({"original_source_medium": "DVD-Video"}, {"encoding_settings": "cabac=1 / ref=5"}, "Movie 2020 DVDRip x264",
     {"source": ["DVDRip"]}),
])
def test_the_source_from_mediainfo(general, video, expected, source):
    tags = search("Movie 2020.mkv", general=general, video=video)
    assert tags.process()[0] == expected
    assert tags.mediainfo_tags == source


@pytest.mark.parametrize("general", [
    # A plain title is not a release name
    {"title": "Charlotte's Web"},
    {"title": "Web"},
    {},
])
def test_no_source_in_mediainfo(general):
    tags = search("Movie 2020.mkv", general=general)
    assert tags.process()[0] == "Movie 2020 H.264"
    assert tags.mediainfo_tags == {}


def test_the_mediainfo_source_decides_the_tracker_type():
    itt = TRACKData.load_from_module(tracker_name="ITT")
    assert itt.filter_type("BluRay REMUX", "Movie 2020 1080p HEVC", "/movies/Movie 2020 1080p HEVC.mkv") == 2
    assert itt.filter_type("WEB-DL", "Movie 2020", "/movies/Movie 2020.mkv") == 4
    assert itt.filter_type(None, "Movie 2020", "/movies/Movie 2020.mkv") == 15
