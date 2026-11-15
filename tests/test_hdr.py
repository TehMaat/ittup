# -*- coding: utf-8 -*-
from types import SimpleNamespace

import pytest

from ittup.common import tags
from ittup.common.tags import SearchTags
from ittup.common.trackers.tags_list import TAGS_LIST

TAGS_POSITION = ["title", "year", "part", "version", "resolution", "uhd", "platform", "source", "remux",
                 "multi", "acodec", "channels", "flag", "subtitle", "hdr", "vcodec"]

WEB_DL = "Movie.2020.1080p.WEB-DL.DDP5.1.HDR.H.265-GRP.mkv"
REMUX = "Movie.2020.2160p.BluRay.REMUX.HEVC.DV.HDR.TrueHD.7.1-GRP.mkv"

# Color fields of a PQ BT.2020 10 bit video (HDR10, HDR10+, Dolby Vision with a HDR10 base layer)
PQ_VIDEO = {"color_primaries": "BT.2020", "matrix_coefficients": "BT.2020 non-constant", "bit_depth": 10,
            "transfer_characteristics": "PQ"}


@pytest.fixture
def warnings(monkeypatch):
    logged = []
    monkeypatch.setattr(tags.custom_console, "bot_warning_log", logged.append)
    monkeypatch.setattr(tags.custom_console, "bot_log", lambda message: None)
    return logged


def build_title(filename: str, **video_fields) -> tuple[str, dict]:
    mediafile = SimpleNamespace(video_track=[{"format": "HEVC", **PQ_VIDEO, **video_fields}], audio_track=[],
                                subtitle_track=[])
    media = SimpleNamespace(mediafile=mediafile, torrent_pack=False, resolution="1080p", pack=None)
    search = SearchTags(filename=filename, title="Movie", year="2020", season=None, episode=None, media=media,
                        tags_position=list(TAGS_POSITION), tags_list=TAGS_LIST, sign_list={},
                        ban_list={"dummy": "banned"}, releaser_sign="")
    return search.process()


def hdr(commercial: str, hdr_format: str, other: str = "", filename: str = WEB_DL) -> str:
    title, tags_dict = build_title(filename, hdr_format_commercial=commercial, hdr_format=hdr_format,
                                   other_hdr_format=[other] if other else [])
    assert "*HDR" not in title
    return tags_dict["hdr"]


def test_dolby_vision_profile_8_with_hdr10plus_without_hdr10_metadata(warnings):
    # Issue #135: no mastering display, so MediaInfo clears the HDR10/HDR10+ compatibility
    other = ("Dolby Vision, Version 1.0, Profile 8, dvhe.08.06, BL+RPU, no metadata compression"
             " / SMPTE ST 2094 App 4, Version 1")
    assert hdr("Dolby Vision / SMPTE ST 2094 App 4", "Dolby Vision / SMPTE ST 2094 App 4", other) == "DV HDR10+"
    assert not warnings


def test_hdr10plus_without_hdr10_metadata(warnings):
    assert hdr("SMPTE ST 2094 App 4", "SMPTE ST 2094 App 4") == "HDR10+"
    assert not warnings


@pytest.mark.parametrize("commercial, hdr_format, expected", [
    ("Dolby Vision", "Dolby Vision", "DV"),
    ("HDR10 / HDR10", "Dolby Vision / SMPTE ST 2086", "DV HDR10"),
    ("HDR10 / HDR10+", "Dolby Vision / SMPTE ST 2094 App 4", "DV HDR10+"),
    ("Blu-ray / HDR10", "Dolby Vision / SMPTE ST 2086", "DV HDR10"),
    ("HDR10", "SMPTE ST 2086", "HDR10"),
    ("HDR10+", "SMPTE ST 2094 App 4", "HDR10+"),
    ("HDR10+ / HDR10", "SMPTE ST 2094 App 4 / SMPTE ST 2086", "HDR10+"),
])
def test_known_formats(warnings, commercial, hdr_format, expected):
    assert hdr(commercial, hdr_format) == expected
    assert not warnings


def test_unknown_format_with_dolby_vision_keeps_dv(warnings):
    assert hdr("Dolby Vision / SL-HDR1", "Dolby Vision / SL-HDR1") == "DV"
    assert any("SL-HDR1" in message for message in warnings)


def test_unknown_format_falls_back_to_hdr(warnings):
    assert hdr("SL-HDR1", "SL-HDR1") == "HDR"
    assert any("SL-HDR1" in message for message in warnings)


def test_pq10_without_hdr_format(warnings):
    _, tags_dict = build_title(WEB_DL)
    assert tags_dict["hdr"] == "PQ10"


def test_hybrid_remux_with_dolby_vision_profile_8(warnings):
    other = ("Dolby Vision, Version 1.0, Profile 8.1, dvhe.08.06, BL+RPU, HDR10 compatible"
             " / SMPTE ST 2086, HDR10 compatible")
    _, tags_dict = build_title(REMUX, hdr_format_commercial="HDR10 / HDR10",
                               hdr_format="Dolby Vision / SMPTE ST 2086", other_hdr_format=[other])
    assert tags_dict["hdr"] == "DV HDR10"
    assert "HYBRID" in tags_dict["remux"]
    assert any("HYBRID REMUX" in message for message in warnings)
