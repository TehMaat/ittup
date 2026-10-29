# -*- coding: utf-8 -*-
import pytest

from ittup.common.utility import ManageTitles


@pytest.mark.parametrize("title, name, spelling", [
    ("Spider Man No Way Home", "Spider-Man.No.Way.Home.2021.1080p.WEB-DL.mkv", "Spider-Man No Way Home"),
    ("Mission Impossible Dead Reckoning", "Mission: Impossible - Dead Reckoning (2023) 1080p.mkv",
     "Mission: Impossible - Dead Reckoning"),
    ("Fast & Furious", "Fast & Furious 2009 1080p BluRay.mkv", "Fast & Furious"),
    ("Ciao! Come Stai", "Ciao! Come Stai 2020 1080p.mkv", "Ciao! Come Stai"),
    ("Il Ragazzo e l Airone", "Il.Ragazzo.e.l'Airone.2023.1080p.mkv", "Il Ragazzo e l'Airone"),
    ("Ocean s Eleven", "Ocean's_Eleven_2001_1080p.mkv", "Ocean's Eleven"),
    ("S W A T", "S.W.A.T.2017.S01.1080p", "S.W.A.T"),
    ("Mr Robot", "Mr. Robot S01 1080p", "Mr. Robot"),
    # Not in the name: the guessit title
    ("Some Title", "Other.Name.2020.mkv", "Some Title"),
    (None, "Other.Name.2020.mkv", None),
])
def test_original_spelling(title, name, spelling):
    assert ManageTitles.original_spelling(title, name) == spelling


def test_italian_title_from_tmdb():
    from ittup.core.media_manager.VideoManager import VideoManager
    assert VideoManager.italian_title({"title": "Spider-Man: No Way Home"}) == "Spider-Man: No Way Home"
    assert VideoManager.italian_title({"name": "La casa di carta"}) == "La casa di carta"
    assert VideoManager.italian_title({"title": "Città di Dio"}) == "Città di Dio"
    # No Italian translation: the original title in another script
    assert VideoManager.italian_title({"title": "千と千尋の神隠し"}) is None
    assert VideoManager.italian_title({"title": ""}) is None
    assert VideoManager.italian_title(None) is None


def test_the_tmdb_title_replaces_the_file_name_title():
    from types import SimpleNamespace
    from ittup.common.tags import SearchTags
    from ittup.common.trackers.tags_list import TAGS_LIST
    mediafile = SimpleNamespace(video_track=[], audio_track=[], subtitle_track=[])
    media = SimpleNamespace(mediafile=mediafile, torrent_pack=False, resolution="1080p", pack=None)
    search = SearchTags(filename="Wicked.Part.2.2025.1080p.WEB-DL.mkv", title="Wicked", year=2025, season=None,
                        episode=None, media=media, tags_position=["title", "year", "part", "source"],
                        tags_list=TAGS_LIST, sign_list={}, ban_list={"dummy": "banned"}, releaser_sign="")
    assert search.process()[0] == "Wicked 2025 Part 2 WEB-DL"
    assert search.set_title("Wicked - Parte 2")[0] == "Wicked - Parte 2 2025 WEB-DL"


def test_a_word_with_part_inside_keeps_the_part_tag():
    from types import SimpleNamespace
    from ittup.common.tags import SearchTags
    from ittup.common.trackers.tags_list import TAGS_LIST
    media = SimpleNamespace(mediafile=SimpleNamespace(video_track=[], audio_track=[], subtitle_track=[]),
                            torrent_pack=False, resolution="1080p", pack=None)
    search = SearchTags(filename="Movie.Part.2.2020.mkv", title="Movie", year=2020, season=None, episode=None,
                        media=media, tags_position=["title", "year", "part"], tags_list=TAGS_LIST, sign_list={},
                        ban_list={"dummy": "banned"}, releaser_sign="")
    search.process()
    assert search.set_title("The Departed")[0] == "The Departed 2020 Part 2"


@pytest.mark.parametrize("filename, expected", [
    ("Titolo_1990_BDRip_1080p.mkv", "Titolo 1990 BDRip"),
    ("Titolo_1990_WEB-DL_1080p.mkv", "Titolo 1990 WEB-DL"),
    ("Titolo_1990_WebDL_1080p.mkv", "Titolo 1990 WEB-DL"),
    ("Titolo.1990.(WEB-DL).1080p.mkv", "Titolo 1990 WEB-DL"),
    ("Titolo 1990 [BluRay] 1080p.mkv", "Titolo 1990 BluRay"),
    ("Titolo_1990_Part_2_1080p.mkv", "Titolo 1990 Part 2"),
])
def test_the_source_between_special_characters(filename, expected):
    from types import SimpleNamespace
    from ittup.common.tags import SearchTags
    from ittup.common.trackers.tags_list import TAGS_LIST
    media = SimpleNamespace(mediafile=SimpleNamespace(video_track=[], audio_track=[], subtitle_track=[]),
                            torrent_pack=False, resolution="1080p", pack=None)
    search = SearchTags(filename=filename, title="Titolo", year=1990, season=None, episode=None, media=media,
                        tags_position=["title", "year", "part", "source"], tags_list=TAGS_LIST, sign_list={},
                        ban_list={"dummy": "banned"}, releaser_sign="")
    assert search.process()[0] == expected


@pytest.mark.parametrize("filename, expected", [
    ("Titolo 1990 1080p VU REMUX DTS-HD MA 5.1.mkv", "Titolo 1990 VU REMUX"),
    ("Titolo.1990.1080p.REMUX.VU.mkv", "Titolo 1990 REMUX VU"),
    ("Titolo 1990 1080p BluRay REMUX.mkv", "Titolo 1990 BluRay REMUX"),
])
def test_the_remux_tags_keep_the_order_of_the_name(filename, expected):
    from types import SimpleNamespace
    from ittup.common.tags import SearchTags
    from ittup.common.trackers.tags_list import TAGS_LIST
    media = SimpleNamespace(mediafile=SimpleNamespace(video_track=[], audio_track=[], subtitle_track=[]),
                            torrent_pack=False, resolution="1080p", pack=None)
    search = SearchTags(filename=filename, title="Titolo", year=1990, season=None, episode=None, media=media,
                        tags_position=["title", "year", "source", "remux"], tags_list=TAGS_LIST, sign_list={},
                        ban_list={"dummy": "banned"}, releaser_sign="")
    assert search.process()[0] == expected
