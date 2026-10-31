# -*- coding: utf-8 -*-
from types import SimpleNamespace

from ittup.common.tags import SearchTags
from ittup.common.trackers.tags_list import TAGS_LIST

LANGUAGES = {"ITA": ["Italian", "it", "ita"], "ENG": ["English", "en", "eng"], "FRA": ["French", "fr", "fra"],
             "GER": ["German", "de", "deu"], "JPN": ["Japanese", "ja", "jpn"],
             "SPA": ["Spanish", "es", "spa"], "POR": ["Portuguese", "pt", "por"]}


def track(other_format: str, channel_s: int, language: str | None = None, commercial_name: str = "") -> dict:
    return {"other_format": [other_format], "channel_s": channel_s, "commercial_name": commercial_name,
            "other_language": LANGUAGES[language] if language else []}


def audio_tags(*audio_track: dict, original_language: str | None = None) -> dict:
    mediafile = SimpleNamespace(video_track=[], audio_track=list(audio_track), subtitle_track=[])
    media = SimpleNamespace(mediafile=mediafile, torrent_pack=False, resolution="1080p", pack=None)
    search = SearchTags(filename="Movie.2020.1080p.BluRay.REMUX-GRP.mkv", title="Movie", year="2020", season=None,
                        episode=None, media=media, tags_position=["title", "year", "multi", "acodec"], tags_list=TAGS_LIST,
                        sign_list={}, ban_list={"dummy": "banned"}, releaser_sign="")
    search.process()
    _, tags_dict = search.set_original_language(original_language)
    return tags_dict


def acodec(*audio_track: dict, original_language: str | None = None) -> list:
    return audio_tags(*audio_track, original_language=original_language)["acodec"]


def test_best_ita_and_best_eng():
    assert acodec(track("MLP FBA 16-ch", 8, "ITA", "Dolby TrueHD with Dolby Atmos"), track("DTS XLL", 6, "ITA"),
                  track("AC-3", 6, "ENG"), track("E-AC-3", 6, "ENG"), original_language="en") == [
        "TrueHD 7.1 Atmos", "DD+ 5.1", "ITA", "ENG"]


def test_eng_codec_not_the_original_language():
    assert acodec(track("AC-3", 6, "ITA"), track("E-AC-3", 6, "ENG"), track("DTS XLL", 6, "JPN"),
                  original_language="ja") == ["DD 5.1", "DD+ 5.1", "ITA", "ENG"]


def test_other_languages_are_multi():
    tags = audio_tags(track("AC-3", 6, "FRA"), track("MLP FBA 16-ch", 8, "GER"), track("AC-3", 6, "ITA"),
                      track("AAC LC", 2, "ENG"), original_language="en")
    assert tags["acodec"] == ["DD 5.1", "AAC 2.0", "ITA", "ENG"]
    assert tags["multi"] == "MULTI"


def test_many_languages_keep_only_ita_and_eng():
    languages = ["JPN", "FRA", "GER", "ITA", "ENG", "SPA", "POR"]
    tags = audio_tags(*[track("E-AC-3", 6, language) for language in languages], original_language="ja")
    assert tags["acodec"] == ["DD+ 5.1", "ITA", "ENG"]
    assert tags["multi"] == "MULTI"


def test_two_languages_are_written():
    # Apocalisse Z (2024): Spanish movie, file with Italian and English tracks only
    tags = audio_tags(track("E-AC-3", 6, "ITA"), track("E-AC-3", 6, "ENG"), original_language="es")
    assert tags["acodec"] == ["DD+ 5.1", "ITA", "ENG"]
    assert "multi" not in tags


def test_two_languages_without_eng_are_written():
    tags = audio_tags(track("DTS XLL", 6, "JPN"), track("AC-3", 6, "ITA"), original_language="ja")
    assert tags["acodec"] == ["DD 5.1", "DTS-HD MA 5.1", "ITA", "JPN"]
    assert "multi" not in tags


def test_three_languages_are_multi():
    tags = audio_tags(track("AC-3", 6, "ITA"), track("E-AC-3", 6, "ENG"), track("DTS XLL", 6, "SPA"),
                      original_language="es")
    assert tags["acodec"] == ["DD 5.1", "DD+ 5.1", "ITA", "ENG"]
    assert tags["multi"] == "MULTI"


def test_three_languages_without_eng_write_only_ita():
    tags = audio_tags(track("AC-3", 6, "ITA"), track("AC-3", 6, "FRA"), track("AC-3", 6, "GER"))
    assert tags["acodec"] == ["DD 5.1", "ITA"]
    assert tags["multi"] == "MULTI"


def test_three_languages_without_ita_write_only_eng():
    tags = audio_tags(track("AC-3", 6, "FRA"), track("E-AC-3", 6, "ENG"), track("AC-3", 6, "GER"))
    assert tags["acodec"] == ["DD+ 5.1", "ENG"]
    assert tags["multi"] == "MULTI"


def test_without_ita_and_eng_the_first_language_is_written():
    tags = audio_tags(track("AC-3", 6, "FRA"), track("AC-3", 6, "GER"), track("AC-3", 6, "SPA"))
    assert tags["acodec"] == ["DD 5.1", "FRA"]
    assert tags["multi"] == "MULTI"


def test_one_language():
    tags = audio_tags(track("AC-3", 6, "ITA"), track("DTS XLL", 6, "ITA"), original_language="it")
    assert tags["acodec"] == ["DTS-HD MA 5.1", "ITA"]
    assert "multi" not in tags


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


def test_title_does_not_change_with_the_original_language():
    audio = [track("AC-3", 6, "ITA"), track("E-AC-3", 6, "ENG"), track("DTS XLL", 6, "JPN")]
    mediafile = SimpleNamespace(video_track=[], audio_track=audio, subtitle_track=[])
    media = SimpleNamespace(mediafile=mediafile, torrent_pack=False, resolution="1080p", pack=None)
    search = SearchTags(filename="Movie.2020.1080p.BluRay.REMUX-GRP.mkv", title="Movie", year="2020", season=None,
                        episode=None, media=media, tags_position=["title", "year", "multi", "acodec"],
                        tags_list=TAGS_LIST, sign_list={}, ban_list={"dummy": "banned"}, releaser_sign="")
    title, _ = search.process()
    assert title == "Movie 2020 MULTI DD 5.1 DD+ 5.1 ITA ENG"
    title, _ = search.set_original_language("ja")
    assert title == "Movie 2020 MULTI DD 5.1 DD+ 5.1 ITA ENG"


def test_mono_track():
    assert acodec(track("AAC LC", 1, "ITA")) == ["AAC 1.0", "ITA"]
    assert acodec(track("AC-3", "1", "ITA")) == ["DD 1.0", "ITA"]


def test_unknown_channels_are_not_written():
    assert acodec(track("AC-3", 0, "ITA")) == ["DD", "ITA"]
