# -*- coding: utf-8 -*-
from types import SimpleNamespace

import pytest

from ittup.common import tags
from ittup.common.settings import Validate
from ittup.common.tags import SearchTags
from ittup.common.trackers.tags_list import TAGS_LIST

TAGS_POSITION = ["title", "year", "part", "version", "resolution", "uhd", "platform", "source", "remux",
                 "multi", "acodec", "channels", "flag", "subtitle", "hdr", "vcodec"]

X264_LIBRARY = "x264 core 164 r3095 baee400"
X265_LIBRARY = "x265 3.5+1-f0c1022b6:[Linux][GCC 9.3.0][64 bit] 10bit"


@pytest.fixture
def warnings(monkeypatch):
    logged = []
    monkeypatch.setattr(tags.custom_console, "bot_warning_log", logged.append)
    return logged


def build_title(filename: str, video_format: str | None, writing_library: str = "",
                encoding_settings: str = "", tags_position: list | None = None,
                **video_fields) -> tuple[str, dict]:
    video_track = []
    if video_format:
        video_track.append({"format": video_format, "writing_library": writing_library,
                            "encoding_settings": encoding_settings, **video_fields})
    mediafile = SimpleNamespace(video_track=video_track, audio_track=[], subtitle_track=[])
    media = SimpleNamespace(mediafile=mediafile, torrent_pack=False, resolution="1080p", pack=None)
    search = SearchTags(filename=filename, title="Movie", year="2020", season=None, episode=None, media=media,
                        tags_position=list(tags_position or TAGS_POSITION), tags_list=TAGS_LIST, sign_list={},
                        ban_list={"dummy": "banned"}, releaser_sign="")
    return search.process()


def vcodec(filename: str, video_format: str | None, **kwargs) -> str | None:
    _, tags_dict = build_title(filename, video_format, **kwargs)
    return tags_dict.get("vcodec")


def test_remux_hevc(warnings):
    assert vcodec("Movie.2020.2160p.BluRay.REMUX.HEVC.TrueHD.7.1-GRP.mkv", "HEVC") == "HEVC"
    assert not warnings


def test_remux_with_x265_signature_warns(warnings):
    codec = vcodec("Movie.2020.2160p.BluRay.REMUX.HEVC-GRP.mkv", "HEVC", writing_library=X265_LIBRARY)
    assert codec == "HEVC"
    assert any("fake REMUX" in message for message in warnings)


def test_web_dl_avc_with_x264_signature(warnings):
    codec = vcodec("Movie.2020.1080p.AMZN.WEB-DL.DDP5.1.H.264-GRP.mkv", "AVC", writing_library=X264_LIBRARY)
    assert codec == "H.264"
    assert not warnings


def test_dlmux_is_web_dl():
    assert vcodec("Movie.2020.1080p.DLMux.ITA.ENG.AC3-GRP.mkv", "AVC", writing_library=X264_LIBRARY) == "H.264"


def test_webrip_x265():
    assert vcodec("Movie.2020.1080p.WEBRip.x265-GRP.mkv", "HEVC") == "x265"


def test_encode_x265_is_not_doubled(warnings):
    title, tags_dict = build_title("Movie.2020.1080p.BDRip.x265.10bit-GRP.mkv", "HEVC",
                                   writing_library=X265_LIBRARY)
    assert tags_dict["vcodec"] == "x265"
    assert "video_encoder" not in tags_dict
    assert "H.265" not in title
    assert title.count("x265") == 1
    assert not warnings


def test_bluray_alone_with_x264_signature():
    assert vcodec("Movie.2020.1080p.BluRay.DTS-GRP.mkv", "AVC", writing_library=X264_LIBRARY) == "x264"


def test_bluray_alone_without_signature():
    assert vcodec("Movie.2020.1080p.BluRay.DTS-GRP.mkv", "AVC") == "H.264"


def test_no_release_type_no_signature():
    assert vcodec("Movie.2020.1080p.ITA.ENG-GRP.mkv", "AVC") == "H.264"


def test_signature_from_encoding_settings():
    settings = "cabac=1 / ref=4 / deblock=1:-3:-3 / analyse=0x3:0x133"
    assert vcodec("Movie.2020.1080p.ITA-GRP.mkv", "AVC", encoding_settings=settings) == "x264"


def test_name_and_mediainfo_disagree(warnings):
    codec = vcodec("Movie.2020.1080p.BDRip.x264-GRP.mkv", "HEVC", writing_library=X265_LIBRARY)
    assert codec == "x265"
    assert any("MediaInfo" in message for message in warnings)


def test_family_from_name_without_mediainfo():
    assert vcodec("Movie.2020.1080p.WEBRip.x264-GRP.mkv", None) == "x264"
    assert vcodec("Movie.2020.1080p.BluRay.REMUX.AVC-GRP.mkv", None) == "AVC"


@pytest.mark.parametrize("video_format, video_fields, expected", [
    ("AV1", {}, "AV1"),
    ("VP9", {}, "VP9"),
    ("VC-1", {}, "VC-1"),
    ("MPEG Video", {"format_version": "Version 2"}, "MPEG-2"),
    ("MPEG-4 Visual", {"codec_id": "XVID"}, "XviD"),
])
def test_other_codecs(warnings, video_format, video_fields, expected):
    # The release type rules don't apply to codecs other than 264/265
    assert vcodec("Movie.2020.1080p.BluRay.REMUX-GRP.mkv", video_format, **video_fields) == expected
    assert vcodec("Movie.2020.1080p.WEBRip-GRP.mkv", video_format, writing_library=X264_LIBRARY,
                  **video_fields) == expected
    assert not warnings


def test_video_encoder_in_tags_position():
    position = TAGS_POSITION + ["video_encoder"]
    assert Validate.validate_tags_position(position) == position

    title, tags_dict = build_title("Movie.2020.1080p.WEBRip.x265-GRP.mkv", "HEVC", tags_position=position)
    assert "video_encoder" not in tags_dict
    assert title.lower().count("265") == 1


def test_platform_rip_is_the_platform_and_webrip():
    title, tags_dict = build_title("Movie.2020.1080p.NFRip.x264-GRP.mkv", "AVC", writing_library=X264_LIBRARY)
    assert tags_dict["platform"] == ["NF"]
    assert tags_dict["source"] == ["WEBRip"]
    assert tags_dict["vcodec"] == "x264"
    assert "NF WEBRip" in title
