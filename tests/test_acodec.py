# -*- coding: utf-8 -*-
from types import SimpleNamespace

from ittup.common.tags import SearchTags
from ittup.common.trackers.tags_list import TAGS_LIST

LANGUAGES = {"ITA": ["Italian", "it", "ita"], "ENG": ["English", "en", "eng"], "FRA": ["French", "fr", "fra"],
             "GER": ["German", "de", "deu"]}


def track(other_format: str, channel_s: int, language: str | None = None, commercial_name: str = "") -> dict:
    return {"other_format": [other_format], "channel_s": channel_s, "commercial_name": commercial_name,
            "other_language": LANGUAGES[language] if language else []}


def acodec(*audio_track: dict) -> list:
    mediafile = SimpleNamespace(video_track=[], audio_track=list(audio_track), subtitle_track=[])
    media = SimpleNamespace(mediafile=mediafile, torrent_pack=False, resolution="1080p", pack=None)
    search = SearchTags(filename="Movie.2020.1080p.BluRay.REMUX-GRP.mkv", title="Movie", year="2020", season=None,
                        episode=None, media=media, tags_position=["title", "year", "acodec"], tags_list=TAGS_LIST,
                        sign_list={}, ban_list={"dummy": "banned"}, releaser_sign="")
    _, tags_dict = search.process()
    return tags_dict["acodec"]


def test_keeps_the_two_best_codecs():
    assert acodec(track("AC-3", 6, "ITA"), track("DTS XLL", 6, "ITA"), track("E-AC-3", 6, "ENG"),
                  track("MLP FBA 16-ch", 8, "ENG", "Dolby TrueHD with Dolby Atmos")) == [
        "TrueHD 7.1 Atmos", "DTS-HD MA 5.1", "ITA", "ENG"]


def test_ignores_other_languages():
    assert acodec(track("AC-3", 6, "ITA"), track("MLP FBA 16-ch", 8, "FRA"), track("DTS XLL", 6, "GER"),
                  track("AAC LC", 2, "ENG")) == ["DD 5.1", "AAC 2.0", "ITA", "FRA", "GER", "ENG"]


def test_same_codec_is_written_once():
    assert acodec(track("AC-3", 6, "ITA"), track("AC-3", 6, "ENG")) == ["DD 5.1", "ITA", "ENG"]


def test_channels_break_ties():
    assert acodec(track("AC-3", 2, "ITA"), track("AC-3", 6, "ITA"), track("AAC LC", 2, "ENG")) == [
        "DD 5.1", "DD 2.0", "ITA", "ENG"]


def test_untagged_tracks_are_used_when_no_ita_eng():
    assert acodec(track("AC-3", 6), track("E-AC-3", 6)) == ["DD+ 5.1", "DD 5.1"]
