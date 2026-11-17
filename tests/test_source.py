# -*- coding: utf-8 -*-
from types import SimpleNamespace

import pytest

from ittup.common.tags import SearchTags
from ittup.common.trackers.tags_list import TAGS_LIST
from ittup.common.trackers.trackers import TRACKData

POSITION = ["title", "year", "resolution", "source", "remux", "vcodec"]


def search(filename: str, general: dict | None = None, video: dict | None = None) -> SearchTags:
    mediafile = SimpleNamespace(general_track=general or {}, video_track=[{"format": "AVC", **(video or {})}],
                                audio_track=[], subtitle_track=[])
    media = SimpleNamespace(mediafile=mediafile, torrent_pack=False, resolution="1080p", pack=None)
    return SearchTags(filename=filename, title="Movie", year=2020, season=None, episode=None, media=media,
                      tags_position=POSITION, tags_list=TAGS_LIST, sign_list={}, ban_list={"dummy": "banned"},
                      releaser_sign="")


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


X265_SETTINGS = "cpuid=1111039 / frame-threads=4 / ctu=64 / rc=crf / crf=19.5 / vbv-maxrate=0"


def test_an_x265_encode_without_source_is_a_bluray_encode():
    # Issue #144: H265 in the name, a release name without source in the metadata, x265 signature
    name = "Resident Evil (2026) AC3 5.1 ITA.ENG 1080p H265 sub ita.eng Sp33dy94-MIRCrew"
    tags = search(f"{name}.mkv", general={"movie_name": name},
                  video={"format": "HEVC", "writing_library": "x265 4.1+222-afa0028",
                         "encoding_settings": X265_SETTINGS})
    assert tags.process()[0] == "Movie 2020 BluRay x265"
    assert tags.mediainfo_tags == {"source": ["BluRay"]}
    itt = TRACKData.load_from_module(tracker_name="ITT")
    assert itt.filter_type("BluRay", name, f"/movies/{name}.mkv") == 3


def test_a_codec_in_the_name_without_source_and_signature_is_an_encode():
    # Issue #141: H264 in the name, no source, the x264 header removed from the video track
    name = "Apocalypse Z - New World (2026) 1080p H264 iTA EnG Spa AC3 Sub iTA EnG Spa-MIRCrew"
    tags = search(f"{name}.mkv", general={"movie_name": "Apocalypse Z - New World (2026) MIRCrew"})
    assert tags.process()[0] == "Movie 2020 BluRay x264"
    assert tags.mediainfo_tags == {"source": ["BluRay"]}
    itt = TRACKData.load_from_module(tracker_name="ITT")
    # The type of the source written in the title is the type of the codec in the name: Encode
    assert itt.filter_type("BluRay", name, f"/movies/{name}.mkv") == itt.filter_type(name) == 3


@pytest.mark.parametrize("filename, video", [
    # A signature without the codec in the name
    ("Movie 2020 1080p ITA.mkv", {"encoding_settings": "cabac=1 / ref=5"}),
    # The codec in the name without the signature
    ("Movie 2020 1080p ITA x264.mkv", {}),
])
def test_one_of_signature_and_codec_in_the_name_is_enough(filename, video):
    tags = search(filename, video=video)
    assert tags.process()[0] == "Movie 2020 BluRay x264"
    assert tags.mediainfo_tags == {"source": ["BluRay"]}


@pytest.mark.parametrize("filename, video, expected", [
    # Neither the signature nor the codec in the name: the tracker type is not Encode, the video stays H.264
    ("Movie 2020 1080p ITA.mkv", {}, "Movie 2020 H.264"),
    # Not H.264/H.265
    ("Movie 2020 1080p XviD.mkv", {"format": "MPEG-4 Visual", "codec_id": "XVID"}, "Movie 2020 XviD"),
    # A DVD not encoded again
    ("Movie 2020 576p x264.mkv", {"original_source_medium": "DVD-Video"}, "Movie 2020 H.264"),
])
def test_no_assumed_source(filename, video, expected):
    tags = search(filename, video=video)
    assert tags.process()[0] == expected
    assert tags.mediainfo_tags == {}
    assert tags.assumed_encode is False


def test_the_mediainfo_source_decides_the_tracker_type():
    itt = TRACKData.load_from_module(tracker_name="ITT")
    assert itt.filter_type("BluRay REMUX", "Movie 2020 1080p HEVC", "/movies/Movie 2020 1080p HEVC.mkv") == 2
    assert itt.filter_type("WEB-DL", "Movie 2020", "/movies/Movie 2020.mkv") == 4
    assert itt.filter_type(None, "Movie 2020", "/movies/Movie 2020.mkv") == 15
