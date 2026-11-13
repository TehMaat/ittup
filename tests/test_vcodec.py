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


def search_tags(filename: str, video_format: str | None, writing_library: str = "",
                encoding_settings: str = "", tags_position: list | None = None,
                **video_fields) -> SearchTags:
    video_track = []
    if video_format:
        video_track.append({"format": video_format, "writing_library": writing_library,
                            "encoding_settings": encoding_settings, **video_fields})
    mediafile = SimpleNamespace(video_track=video_track, audio_track=[], subtitle_track=[])
    media = SimpleNamespace(mediafile=mediafile, torrent_pack=False, resolution="1080p", pack=None)
    search = SearchTags(filename=filename, title="Movie", year="2020", season=None, episode=None, media=media,
                        tags_position=list(tags_position or TAGS_POSITION), tags_list=TAGS_LIST, sign_list={},
                        ban_list={"dummy": "banned"}, releaser_sign="")
    search.process()
    return search


def build_title(filename: str, video_format: str | None, **kwargs) -> tuple[str, dict]:
    search = search_tags(filename, video_format, **kwargs)
    return search.ordered_title()


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


def test_a_fake_remux_is_a_review_reason(warnings):
    search = search_tags("Movie.2020.1080p.BluRay.REMUX.AVC-GRP.mkv", "AVC", writing_library=X264_LIBRARY)
    assert search.review_reasons == [f"possible fake REMUX: video encoded with {X264_LIBRARY}"]
    # The warning is still there
    assert any("fake REMUX" in message for message in warnings)
    # The title doesn't change
    assert "REMUX" in search.ordered_title()[0]


def test_a_fake_remux_from_the_encoding_settings_is_a_review_reason(warnings):
    search = search_tags("Movie.2020.1080p.BluRay.REMUX.AVC-GRP.mkv", "AVC", encoding_settings="cabac=1 / ref=4")
    assert search.review_reasons == ["possible fake REMUX: video encoded with x264"]


@pytest.mark.parametrize("filename, video_format, writing_library", [
    ("Movie.2020.2160p.BluRay.REMUX.HEVC-GRP.mkv", "HEVC", ""),
    ("Movie.2020.1080p.AMZN.WEB-DL.DDP5.1.H.264-GRP.mkv", "AVC", X264_LIBRARY),
    ("Movie.2020.1080p.BluRay.x265-GRP.mkv", "HEVC", X265_LIBRARY),
    ("Movie.2020.1080p.WEBRip.x264-GRP.mkv", "AVC", X264_LIBRARY),
])
def test_no_review_reason(warnings, filename, video_format, writing_library):
    assert search_tags(filename, video_format, writing_library=writing_library).review_reasons == []


def test_hdr_warnings_are_not_review_reasons(warnings):
    # Unknown HDR format and HYBRID REMUX: only warnings
    search = search_tags("Movie.2020.2160p.BluRay.REMUX.HEVC-GRP.mkv", "HEVC",
                         hdr_format_commercial="Dolby Vision / Brand New HDR", hdr_format="Dolby Vision",
                         other_hdr_format=["dvhe.08.06"])
    assert any("HDR Warning" in message for message in warnings)
    assert any("HYBRID REMUX" in message for message in warnings)
    assert search.review_reasons == []
    # PQ10 warning
    search = search_tags("Movie.2020.2160p.BluRay.REMUX.HEVC-GRP.mkv", "HEVC", color_primaries="BT.2020",
                         matrix_coefficients="BT.2020 non-constant", bit_depth=8, transfer_characteristics="PQ")
    assert any("PQ10" in message for message in warnings)
    assert search.review_reasons == []


# The x264 settings of the 'Kraken' WEB-DL of #137: CRF, no VBV
X264_CRF = ("cabac=1 / ref=4 / deblock=1:0:0 / analyse=0x3:0x113 / me=hex / subme=7 / psy=1 / psy_rd=1.00:0.00"
            " / mixed_ref=1 / me_range=16 / chroma_me=1 / trellis=1 / 8x8dct=1 / cqm=0 / deadzone=21,11"
            " / fast_pskip=1 / chroma_qp_offset=-2 / threads=34 / lookahead_threads=5 / sliced_threads=0 / nr=0"
            " / decimate=1 / interlaced=0 / bluray_compat=0 / constrained_intra=0 / bframes=3 / b_pyramid=2"
            " / b_adapt=1 / b_bias=0 / direct=1 / weightb=1 / open_gop=0 / weightp=2 / keyint=250 / keyint_min=23"
            " / scenecut=40 / intra_refresh=0 / rc_lookahead=50 / rc=crf / mbtree=1 / crf=21.0 / qcomp=0.60"
            " / qpmin=0 / qpmax=69 / qpstep=4 / ip_ratio=1.40 / aq=1:1.00")
X264_CAPPED_CRF = X264_CRF.replace(" / qcomp=0.60", " / qcomp=0.60 / vbv_maxrate=8000 / vbv_bufsize=16000")
X264_2PASS = X264_CRF.replace("rc=crf / mbtree=1 / crf=21.0", "rc=2pass / mbtree=1 / bitrate=3270 / ratetol=1.0")
X264_ABR = X264_CRF.replace("rc=crf / mbtree=1 / crf=21.0", "rc=abr / mbtree=1 / bitrate=3270 / ratetol=1.0")
X265_CRF = ("cpuid=1111039 / frame-threads=4 / numa-pools=16 / wpp / no-pmode / no-pme / no-psnr / no-ssim"
            " / log-level=2 / input-csp=1 / input-res=1920x1080 / interlace=0 / total-frames=0 / level-idc=0"
            " / ctu=64 / min-cu-size=8 / max-tu-size=32 / rc=crf / crf=22.0 / qcomp=0.60 / qpstep=4"
            " / stats-write=0 / stats-read=0 / vbv-maxrate=0 / vbv-bufsize=0 / vbv-init=0.9 / crf-max=0.0"
            " / crf-min=0.0 / ipratio=1.40 / pbratio=1.30 / aq-mode=2 / aq-strength=1.00")
X265_CAPPED_CRF = X265_CRF.replace("vbv-maxrate=0 / vbv-bufsize=0", "vbv-maxrate=10000 / vbv-bufsize=20000")


@pytest.mark.parametrize("video, expected", [
    ({"writing_library": "x264 core 165 r3223 0480cb0", "encoding_settings": X264_CRF}, "x264 crf=21.0, no VBV"),
    ({"writing_library": X265_LIBRARY, "encoding_settings": X265_CRF}, "x265 crf=22.0, no VBV"),
    ({"encoding_settings": X264_CRF}, "x264 crf=21.0, no VBV"),
    ({"writing_library": X264_LIBRARY, "encoding_settings": X264_CAPPED_CRF}, None),
    ({"writing_library": X265_LIBRARY, "encoding_settings": X265_CAPPED_CRF}, None),
    ({"writing_library": X264_LIBRARY, "encoding_settings": X264_2PASS}, None),
    ({"writing_library": X264_LIBRARY, "encoding_settings": X264_ABR}, None),
    ({"writing_library": X264_LIBRARY}, None),
    ({"writing_library": X264_LIBRARY, "encoding_settings": "rc=crf / vbv_maxrate=n/a"}, None),
    ({}, None),
])
def test_home_encode_settings(video, expected):
    assert SearchTags.home_encode_settings(video) == expected


def test_web_dl_encoded_with_crf_is_a_possible_webrip(warnings):
    search = search_tags("Kraken (2026) iTA.WEBDL.1080p.x264-Dr4gon.mkv", "AVC",
                         writing_library="x264 core 165 r3223 0480cb0", encoding_settings=X264_CRF)
    # The title doesn't change: the staff decides
    assert search.tags_dict["vcodec"] == "H.264"
    assert search.tags_dict["source"] == ["WEB-DL"]
    assert search.ordered_title()[0].endswith("WEB-DL SDR H.264")
    webrip = [message for message in warnings if "possible WEBRip" in message]
    assert len(webrip) == 1 and "crf=21.0" in webrip[0]
    assert search.review_reasons == ["possible WEBRip: x264 crf=21.0, no VBV"]


def test_web_dl_hevc_encoded_with_crf_is_a_possible_webrip(warnings):
    search = search_tags("Movie.2020.1080p.WEB-DL.x265-GRP.mkv", "HEVC", writing_library=X265_LIBRARY,
                         encoding_settings=X265_CRF)
    assert search.tags_dict["vcodec"] == "H.265"
    assert sum("possible WEBRip" in message for message in warnings) == 1
    assert search.review_reasons == ["possible WEBRip: x265 crf=22.0, no VBV"]


@pytest.mark.parametrize("encoding_settings", [X264_CAPPED_CRF, X264_2PASS, X264_ABR, ""])
def test_web_dl_with_the_settings_of_a_service(warnings, encoding_settings):
    search = search_tags("Movie.2020.1080p.AMZN.WEB-DL.DDP5.1.H.264-GRP.mkv", "AVC",
                         writing_library=X264_LIBRARY, encoding_settings=encoding_settings)
    assert search.tags_dict["vcodec"] == "H.264"
    assert not warnings
    assert search.review_reasons == []


def test_dlmux_encoded_with_crf_is_a_possible_webrip(warnings):
    search = search_tags("Movie.2020.1080p.DLMux.ITA.ENG.AC3-GRP.mkv", "AVC", writing_library=X264_LIBRARY,
                         encoding_settings=X264_CRF)
    assert search.tags_dict["vcodec"] == "H.264"
    assert any("possible WEBRip" in message for message in warnings)
    assert search.review_reasons == ["possible WEBRip: x264 crf=21.0, no VBV"]


@pytest.mark.parametrize("filename, expected", [
    ("Movie.2020.1080p.WEBRip.x264-GRP.mkv", "x264"),
    ("Movie.2020.1080p.BDRip.x264-GRP.mkv", "x264"),
    ("Movie.2020.1080p.BluRay.x264-GRP.mkv", "x264"),
    ("Movie.2020.1080p.HDTV.x264-GRP.mkv", "H.264"),
])
def test_crf_is_normal_on_an_encode(warnings, filename, expected):
    search = search_tags(filename, "AVC", writing_library=X264_LIBRARY, encoding_settings=X264_CRF)
    assert search.tags_dict["vcodec"] == expected
    assert not any("possible WEBRip" in message for message in warnings)
    assert search.review_reasons == []


def test_fake_remux_with_crf_is_still_a_fake_remux(warnings):
    search = search_tags("Movie.2020.1080p.BluRay.REMUX.AVC-GRP.mkv", "AVC", writing_library=X264_LIBRARY,
                         encoding_settings=X264_CRF)
    assert search.tags_dict["vcodec"] == "AVC"
    assert not any("possible WEBRip" in message for message in warnings)
    assert search.review_reasons == [f"possible fake REMUX: video encoded with {X264_LIBRARY}"]
