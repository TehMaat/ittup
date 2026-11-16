# -*- coding: utf-8 -*-
import argparse

import pytest

from ittup.common.rename import is_valid_name, rename_invalid, safe_name
from ittup.core.media_manager.ContentManager import ContentManager


@pytest.mark.parametrize("name, safe", [
    ("Mission: Impossible - Dead Reckoning 2023 1080p.mkv", "Mission - Impossible - Dead Reckoning 2023 1080p.mkv"),
    ("Titolo: Sub 2023", "Titolo - Sub 2023"),
    ("Mission:Impossible.2023.1080p.mkv", "Mission.Impossible.2023.1080p.mkv"),
    ("Che cosa? 2020 1080p.mkv", "Che cosa 2020 1080p.mkv"),
    ('Il "film" * 2020.mkv', "Il film 2020.mkv"),
    ("Cartella finita con il punto.", "Cartella finita con il punto"),
    ("Mr. Robot S01", "Mr. Robot S01"),
    # Dash and exclamation mark are valid
    ("Ciao! Spider-Man 2020.mkv", "Ciao! Spider-Man 2020.mkv"),
])
def test_safe_name(name, safe):
    assert safe_name(name) == safe
    assert is_valid_name(safe)


def test_rename_a_folder_and_its_files(tmp_path):
    folder = tmp_path / "Show: The Series S01 1080p"
    (folder / "Extras?").mkdir(parents=True)
    (folder / "Show: The Series S01E01.mkv").write_bytes(b"1")
    (folder / "Extras?" / "Making of: part 1.mkv").write_bytes(b"2")
    (folder / "Valid S01E02.mkv").write_bytes(b"3")

    new_path = rename_invalid(str(folder))

    renamed = tmp_path / "Show - The Series S01 1080p"
    assert new_path == str(renamed)
    assert sorted(p.relative_to(renamed).as_posix() for p in renamed.rglob("*")) == [
        "Extras", "Extras/Making of - part 1.mkv", "Show - The Series S01E01.mkv", "Valid S01E02.mkv"]


def test_a_valid_file_is_not_renamed(tmp_path):
    movie = tmp_path / "Movie 2020 1080p.mkv"
    movie.write_bytes(b"")
    assert rename_invalid(str(movie)) == str(movie)
    assert movie.exists()


def test_content_manager_uses_the_renamed_folder(tmp_path):
    folder = tmp_path / "Movie: Part 2020 1080p WEB-DL"
    folder.mkdir()
    (folder / "Movie: Part 2020 1080p WEB-DL.mkv").write_bytes(b"x")
    cli = argparse.Namespace(force=None)

    contents = ContentManager(path=str(folder), mode="folder", cli=cli).process()

    assert len(contents) == 1
    media = contents[0]
    renamed = tmp_path / "Movie - Part 2020 1080p WEB-DL"
    assert media.torrent_path == str(renamed)
    assert media.torrent_name == "Movie - Part 2020 1080p WEB-DL"
    assert media.file_name == str(renamed / "Movie - Part 2020 1080p WEB-DL.mkv")
    assert '"Movie - Part 2020 1080p WEB-DL.mkv"' in media.metainfo


from ittup.common.rename import episode_name, title_name
from ittup.core.media_manager.VideoManager import VideoManager


def test_title_name_with_dots():
    assert title_name("Spider-Man: No Way Home 2021 1080p WEB-DL DD+ 5.1 ITA ENG H.264-SIGN") == \
        "Spider-Man.No.Way.Home.2021.1080p.WEB-DL.DD+.5.1.ITA.ENG.H.264-SIGN"
    assert title_name("Mission: Impossible - Dead Reckoning 2023 1080p") == \
        "Mission.Impossible.Dead.Reckoning.2023.1080p"


def test_episode_name():
    assert episode_name("Show.S04.1080p.WEB-DL", "S04", 4, 2) == "Show.S04E02.1080p.WEB-DL"
    assert episode_name("Show.S04E01-06.1080p", "S04E01-06", 4, 3) == "Show.S04E03.1080p"
    assert episode_name("Show.1080p", "S04", 4, 2) is None
    assert episode_name("Show.S04.1080p", "S04", 4, None) is None


def contents(path, mode="folder"):
    return ContentManager(path=str(path), mode=mode, cli=argparse.Namespace(force=None)).process()


def test_rename_a_single_file(tmp_path):
    (tmp_path / "movie.2020.1080p.web-dl.mkv").write_bytes(b"x")
    media = contents(tmp_path / "movie.2020.1080p.web-dl.mkv", mode="man")[0]
    media.display_name = "Movie: Il Film 2020 1080p WEB-DL H.264"

    VideoManager.rename_files(media)

    new_file = tmp_path / "Movie.Il.Film.2020.1080p.WEB-DL.H.264.mkv"
    assert new_file.exists()
    assert media.torrent_path == media.file_name == str(new_file)
    assert media.torrent_name == new_file.name
    assert str(new_file) in media.metainfo
    assert media.category == "movie"


def test_rename_a_season_pack(tmp_path):
    folder = tmp_path / "show.s04.1080p.web-dl"
    folder.mkdir()
    for name in ["show.s04e01.1080p.mkv", "show.s04e02.1080p.mkv", "notes.txt"]:
        (folder / name).write_bytes(b"x")
    media = contents(folder)[0]
    media.display_name = "Show S04 1080p WEB-DL H.264"

    VideoManager.rename_files(media)

    new_folder = tmp_path / "Show.S04.1080p.WEB-DL.H.264"
    assert sorted(p.name for p in new_folder.iterdir()) == [
        "Show.S04E01.1080p.WEB-DL.H.264.mkv", "Show.S04E02.1080p.WEB-DL.H.264.mkv", "notes.txt"]
    assert media.torrent_path == str(new_folder)
    assert media.torrent_name == "Show.S04.1080p.WEB-DL.H.264"
    assert media.file_name == str(new_folder / "Show.S04E01.1080p.WEB-DL.H.264.mkv")
    assert '"Show.S04E02.1080p.WEB-DL.H.264.mkv"' in media.metainfo
    assert (media.category, media.guess_season, media.torrent_pack) == ("tv", 4, True)


def test_a_season_folder_with_an_e_and_a_number_in_the_group_is_a_pack(tmp_path):
    # #114: the 'e7' in 'byMe7alh' is not an episode
    folder = tmp_path / "S02" / "Show S02 (720p Ita Eng Spa SubS) byMe7alh"
    folder.mkdir(parents=True)
    for name in ["Show S02E01 720p.mkv", "Show S02E02 720p.mkv"]:
        (folder / name).write_bytes(b"x")
    media = contents(folder)[0]

    assert (media.category, media.torrent_pack, media.pack) == ("tv", True, "S02")


def test_a_folder_with_more_movies_keeps_the_file_names(tmp_path):
    folder = tmp_path / "saga"
    folder.mkdir()
    for name in ["movie.one.2001.mkv", "movie.two.2003.mkv"]:
        (folder / name).write_bytes(b"x")
    media = contents(folder)[0]
    media.display_name = "Saga 1080p"

    VideoManager.rename_files(media)

    assert sorted(p.name for p in (tmp_path / "Saga.1080p").iterdir()) == ["movie.one.2001.mkv", "movie.two.2003.mkv"]


from ittup.common.rename import TitleInfo, plan_name, rename_to_title

TITLE = "Spider-Man.No.Way.Home.2021.1080p.WEB-DL.DD+.5.1.ITA.ENG.H.264"
INFO = TitleInfo(resolution="1080p", family="264", source="WEB-DL", year=2021)


@pytest.mark.parametrize("name, new_name", [
    # Only the title: renamed without checking
    ("Spider-Man No Way Home (2021)", TITLE),
    ("spiderman", TITLE),
    # Information that doesn't match MediaInfo or is missing: renamed as the title
    ("Spider-Man.No.Way.Home.2021.720p.WEB-DL.DDP5.1.H.264", TITLE),
    ("Spider-Man.No.Way.Home.2021.1080p.WEB-DL.DDP5.1.x265", TITLE),
    ("Spider-Man.No.Way.Home.2021.1080p.WEB-DL", TITLE),
    # Everything but the source: the source is added in the style of the name
    ("Spider-Man.No.Way.Home.2021.1080p.DDP5.1.H.264-GRP", "Spider-Man.No.Way.Home.2021.1080p.WEB-DL.DDP5.1.H.264-GRP"),
    ("Spider-Man No Way Home 2021 1080p EAC3 x264", "Spider-Man No Way Home 2021 1080p WEB-DL EAC3 x264"),
    ("Spider_Man_2021_1080p_AAC_H264", "Spider_Man_2021_1080p_WEB-DL_AAC_H264"),
    # Complete: kept
    ("Spider-Man.No.Way.Home.2021.1080p.WEB-DL.AAC.2.0.H.264-GRP", None),
    (TITLE, None),
])
def test_plan_name(name, new_name):
    assert plan_name(name, TITLE, INFO).new_name == new_name


def test_no_source_to_add():
    plan = plan_name("Movie.2020.1080p.DDP5.1.H.264-GRP", "Movie.2020.1080p.H.264", TitleInfo(resolution="1080p"))
    assert plan.new_name is None
    assert "source" in plan.reason


def test_a_complete_name_is_kept(tmp_path):
    movie = tmp_path / "Movie.2020.1080p.WEB-DL.DDP5.1.H.264-GRP.mkv"
    movie.write_bytes(b"x")
    new_path, renamed = rename_to_title(str(movie), "Movie 2020 1080p WEB-DL DD+ 5.1 ITA H.264", [], None, {},
                                        TitleInfo(resolution="1080p", family="264", source="WEB-DL", year=2020))
    assert (new_path, renamed) == (str(movie), {})
    assert movie.exists()


def test_the_missing_source_is_added_to_the_pack(tmp_path):
    folder = tmp_path / "Show.S01.1080p.DDP5.1.H.264-GRP"
    folder.mkdir()
    for name in ["Show.S01E01.1080p.DDP5.1.H.264-GRP.mkv", "show.s01e02.mkv"]:
        (folder / name).write_bytes(b"x")
    new_path, renamed = rename_to_title(
        str(folder), "Show S01 1080p WEB-DL DD+ 5.1 ITA H.264", ["Show.S01E01.1080p.DDP5.1.H.264-GRP.mkv",
                                                                 "show.s01e02.mkv"], "S01",
        {"Show.S01E01.1080p.DDP5.1.H.264-GRP.mkv": (1, 1), "show.s01e02.mkv": (1, 2)},
        TitleInfo(resolution="1080p", family="264", source="WEB-DL"))
    assert new_path == str(tmp_path / "Show.S01.1080p.WEB-DL.DDP5.1.H.264-GRP")
    assert renamed == {"Show.S01E01.1080p.DDP5.1.H.264-GRP.mkv": "Show.S01E01.1080p.WEB-DL.DDP5.1.H.264-GRP.mkv",
                       "show.s01e02.mkv": "Show.S01E02.1080p.WEB-DL.DD+.5.1.ITA.H.264.mkv"}


def test_title_info_from_the_tags():
    from types import SimpleNamespace
    from ittup.common.tags import SearchTags
    mediafile = SimpleNamespace(general_track={}, video_track=[{"format": "HEVC"}], audio_track=[], subtitle_track=[])
    media = SimpleNamespace(mediafile=mediafile, torrent_pack=False, resolution="2160p", pack=None)
    search = SearchTags(filename="Movie.2020.2160p.BluRay.REMUX.mkv", title="Movie", year=2020, season=None,
                        episode=None, media=media, tags_position=["title", "year", "source", "remux", "vcodec"],
                        releaser_sign="")
    search.process()
    assert search.title_info() == TitleInfo(resolution="2160p", family="265", source="BluRay REMUX", year=2020)
