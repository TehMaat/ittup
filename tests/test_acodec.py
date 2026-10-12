# -*- coding: utf-8 -*-
from types import SimpleNamespace

from ittup.common.tags import SearchTags
from ittup.common.trackers.tags_list import TAGS_LIST

LANGUAGES = {"ITA": ["Italian", "it", "ita"], "ENG": ["English", "en", "eng"], "FRA": ["French", "fr", "fra"],
             "GER": ["German", "de", "deu"], "JPN": ["Japanese", "ja", "jpn"]}


def track(other_format: str, channel_s: int, language: str | None = None, commercial_name: str = "") -> dict:
    return {"other_format": [other_format], "channel_s": channel_s, "commercial_name": commercial_name,
            "other_language": LANGUAGES[language] if language else []}


def acodec(*audio_track: dict, original_language: str | None = None) -> list:
    mediafile = SimpleNamespace(video_track=[], audio_track=list(audio_track), subtitle_track=[])
    media = SimpleNamespace(mediafile=mediafile, torrent_pack=False, resolution="1080p", pack=None)
    search = SearchTags(filename="Movie.2020.1080p.BluRay.REMUX-GRP.mkv", title="Movie", year="2020", season=None,
                        episode=None, media=media, tags_position=["title", "year", "acodec"], tags_list=TAGS_LIST,
                        sign_list={}, ban_list={"dummy": "banned"}, releaser_sign="")
    search.process()
    _, tags_dict = search.set_original_language(original_language)
    return tags_dict["acodec"]


def test_best_ita_and_best_eng():
    assert acodec(track("MLP FBA 16-ch", 8, "ITA", "Dolby TrueHD with Dolby Atmos"), track("DTS XLL", 6, "ITA"),
                  track("AC-3", 6, "ENG"), track("E-AC-3", 6, "ENG"), original_language="en") == [
        "TrueHD 7.1 Atmos", "DD+ 5.1", "ITA", "ENG"]


def test_original_language_codec():
    assert acodec(track("AC-3", 6, "ITA"), track("E-AC-3", 6, "ENG"), track("DTS XLL", 6, "JPN"),
                  original_language="ja") == ["DD 5.1", "DTS-HD MA 5.1", "ITA", "JPN", "ENG"]


def test_other_languages_only_add_the_flag():
    assert acodec(track("AC-3", 6, "FRA"), track("MLP FBA 16-ch", 8, "GER"), track("AC-3", 6, "ITA"),
                  track("AAC LC", 2, "ENG"), original_language="en") == [
        "DD 5.1", "AAC 2.0", "ITA", "ENG", "FRA", "GER"]


def test_unknown_original_language_is_english():
    assert acodec(track("AC-3", 6, "ITA"), track("E-AC-3", 6, "ENG"), track("DTS XLL", 6, "JPN")) == [
        "DD 5.1", "DD+ 5.1", "ITA", "ENG", "JPN"]


def test_italian_original_language():
    assert acodec(track("AC-3", 6, "ITA"), track("DTS XLL", 6, "ITA"), track("E-AC-3", 6, "ENG"),
                  original_language="it") == ["DTS-HD MA 5.1", "ITA", "ENG"]


def test_channels_break_ties():
    assert acodec(track("AC-3", 2, "ITA"), track("AC-3", 6, "ITA")) == ["DD 5.1", "ITA"]


def test_same_codec_is_written_once():
    assert acodec(track("AC-3", 6, "ITA"), track("AC-3", 6, "ENG")) == ["DD 5.1", "ITA", "ENG"]


def test_untagged_tracks_fill_up_to_two():
    assert acodec(track("AC-3", 6, "ITA"), track("AAC LC", 2), track("DTS XLL", 6)) == [
        "DD 5.1", "DTS-HD MA 5.1", "ITA"]
    assert acodec(track("AC-3", 6, "ITA"), track("AAC LC", 2, "ENG"), track("DTS XLL", 6)) == [
        "DD 5.1", "AAC 2.0", "ITA", "ENG"]
    assert acodec(track("AC-3", 6, "ITA"), track("AC-3", 6, "ENG"), track("DTS XLL", 6)) == [
        "DD 5.1", "DTS-HD MA 5.1", "ITA", "ENG"]


def test_untagged_tracks_only():
    assert acodec(track("AC-3", 6), track("AAC LC", 2), track("E-AC-3", 6)) == ["DD+ 5.1", "DD 5.1"]


def test_title_is_rebuilt_with_the_original_language():
    audio = [track("AC-3", 6, "ITA"), track("E-AC-3", 6, "ENG"), track("DTS XLL", 6, "JPN")]
    mediafile = SimpleNamespace(video_track=[], audio_track=audio, subtitle_track=[])
    media = SimpleNamespace(mediafile=mediafile, torrent_pack=False, resolution="1080p", pack=None)
    search = SearchTags(filename="Movie.2020.1080p.BluRay.REMUX-GRP.mkv", title="Movie", year="2020", season=None,
                        episode=None, media=media, tags_position=["title", "year", "multi", "acodec"],
                        tags_list=TAGS_LIST, sign_list={}, ban_list={"dummy": "banned"}, releaser_sign="")
    title, _ = search.process()
    assert title == "Movie 2020 MULTI DD 5.1 DD+ 5.1 ITA ENG JPN"
    title, _ = search.set_original_language("ja")
    assert title == "Movie 2020 MULTI DD 5.1 DTS-HD MA 5.1 ITA JPN ENG"
