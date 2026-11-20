# -*- coding: utf-8 -*-
"""A .iso without video is a game, whatever the crew or the platform in the name (#170)"""
import argparse
import json
import os

import pytest

from ittup.core import media as media_module
from ittup.core.media import Media
from ittup.core.media_manager import ContentManager as content_manager_module
from ittup.core.media_manager.ContentManager import ContentManager

RELEASE = "STAR.WARS.Galactic.Racer-voices38"
ISO = f"{RELEASE}.iso"
SCENE_NFO = b"\xdb\xdb\xdb VOICES38 presents STAR WARS Galactic Racer \xdb\xdb\xdb\r\n"
KODI_NFO = b'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n<movie><title>Movie</title></movie>\n'


class MediaFile:
    """MediaInfo of the test files: only a DVD image has a video track"""

    def __init__(self, file_path: str):
        self.file_path = file_path

    @property
    def video_track(self) -> list:
        return [{"width": 720, "height": 576}] if "DVD" in os.path.basename(self.file_path) else []


@pytest.fixture(autouse=True)
def mediainfo(monkeypatch):
    monkeypatch.setattr(media_module, "MediaFile", MediaFile)


@pytest.fixture
def warnings(monkeypatch):
    messages: list[str] = []
    monkeypatch.setattr(content_manager_module.custom_console, "bot_warning_log", messages.append)
    return messages


def contents(path, mode="folder", force=None):
    return ContentManager(path=str(path), mode=mode, cli=argparse.Namespace(force=force)).process()


def game_release(folder, nfo="voices38.nfo", content=SCENE_NFO, image=ISO):
    folder.mkdir(parents=True)
    (folder / image).write_bytes(b"\x00" * 2048)
    if nfo:
        (folder / nfo).write_bytes(content)
    return folder


def files(media) -> list[str]:
    return [item["path"][0] for item in json.loads(media.metainfo)]


def test_the_folder_of_an_iso_is_a_game_with_its_nfo(tmp_path):
    folder = game_release(tmp_path / RELEASE)

    [media] = contents(folder)

    assert media.category == "game"
    assert files(media) == [ISO, "voices38.nfo"]
    assert media.nfo == str(folder / "voices38.nfo")


def test_a_single_iso_file_is_a_game(tmp_path, warnings):
    game_release(tmp_path / RELEASE, nfo=None)

    [media] = contents(tmp_path / RELEASE / ISO, mode="man")

    assert media.category == "game"
    assert media.nfo == ''
    assert media.resolution == "altro"
    assert warnings == []


def test_scan_uploads_the_folder_of_an_iso_as_a_game(tmp_path):
    folder = game_release(tmp_path / RELEASE)
    (tmp_path / "Movie.2020.1080p.BluRay.x264-GRP.mkv").write_bytes(b"x")

    category = {media.torrent_name: media.category for media in contents(tmp_path, mode="auto")}

    assert category == {RELEASE: "game", "Movie.2020.1080p.BluRay.x264-GRP.mkv": "movie"}
    assert {media.torrent_name: media.nfo for media in contents(tmp_path, mode="auto")}[RELEASE] == \
        str(folder / "voices38.nfo")


def test_an_iso_with_a_video_track_is_not_a_game(tmp_path):
    (tmp_path / "Movie.2001.DVD.iso").write_bytes(b"x")
    game_release(tmp_path / "Movie.2001.DVD9", nfo=None, image="Movie.2001.DVD9.iso")

    assert not Media.iso_without_video(str(tmp_path / "Movie.2001.DVD.iso"))
    assert not Media.iso_without_video(str(tmp_path / "Movie.2001.DVD9"))
    assert Media(folder=str(tmp_path), subfolder="Movie.2001.DVD.iso").category == "movie"


def test_a_folder_with_a_video_file_is_not_an_iso_game(tmp_path):
    folder = game_release(tmp_path / "Movie.2020.1080p.BluRay.x264-GRP", nfo="grp.nfo")
    (folder / "movie.mkv").write_bytes(b"x")

    assert not Media.iso_without_video(str(folder))
    assert contents(folder)[0].category == "movie"


def test_other_files_and_folders_are_not_iso_games(tmp_path):
    (tmp_path / "Movie.2020.mkv").write_bytes(b"x")
    (tmp_path / "Empty").mkdir()

    assert not Media.iso_without_video(str(tmp_path / "Movie.2020.mkv"))
    assert not Media.iso_without_video(str(tmp_path / "Empty"))
    assert not Media.iso_without_video(str(tmp_path / "missing.iso"))


def test_a_game_of_a_known_crew_is_still_a_game(tmp_path):
    folder = tmp_path / "Some.Game-RUNE"
    folder.mkdir()
    (folder / "setup.exe").write_bytes(b"x")

    assert contents(folder)[0].category == "game"


def test_force_wins_over_the_iso(tmp_path):
    game_release(tmp_path / RELEASE, nfo=None)

    assert contents(tmp_path / RELEASE / ISO, mode="man", force="movie")[0].category == "movie"


def test_a_single_file_warns_about_the_release_nfo_next_to_it(tmp_path, warnings):
    folder = game_release(tmp_path / RELEASE)

    contents(folder / ISO, mode="man")

    assert len(warnings) == 1
    assert "voices38.nfo" in warnings[0] and f'-f "{folder}"' in warnings[0]


def test_the_nfo_warning_is_given_once_per_folder(tmp_path, warnings):
    folder = tmp_path / "Show.S01.1080p.WEB.h264-GRP"
    folder.mkdir()
    for episode in (1, 2):
        (folder / f"show.s01e0{episode}.1080p.web.h264-grp.mkv").write_bytes(b"x")
    (folder / "show.s01.1080p.web.h264-grp.nfo").write_bytes(SCENE_NFO)

    assert len(contents(folder, mode="man")) == 2
    assert len(warnings) == 1


@pytest.mark.parametrize("nfo, content", [(None, None), ("movie.nfo", KODI_NFO)])
def test_no_nfo_warning_without_a_release_nfo(tmp_path, warnings, nfo, content):
    folder = game_release(tmp_path / RELEASE, nfo=nfo, content=content)

    contents(folder / ISO, mode="man")

    assert warnings == []


def test_no_nfo_warning_for_a_folder(tmp_path, warnings):
    contents(game_release(tmp_path / RELEASE))

    assert warnings == []


class NoVideo:
    video_width = "Unknown"


def test_a_file_without_video_suggests_force_game(monkeypatch):
    errors: list[str] = []
    monkeypatch.setattr(media_module.custom_console, "bot_error_log", errors.append)
    monkeypatch.setattr(Media, "mediafile", NoVideo())
    media = Media(folder="", subfolder=ISO)
    media.file_name = ISO

    with pytest.raises(SystemExit):
        _ = media._resolution2

    assert len(errors) == 1
    assert "no video track" in errors[0] and "-force game" in errors[0]
    assert "corrupted" not in errors[0]
