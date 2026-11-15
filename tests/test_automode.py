# -*- coding: utf-8 -*-
import os
from pathlib import Path

from ittup.core.automode import Auto

SHOW = "Show.1080p.WEB-DL"


def video(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"0")


def series(root: Path, name: str = SHOW) -> Path:
    """ A series with a folder for each season, and no video file of its own """
    for season in (2, 1):
        video(root / name / f"Show.S0{season}.1080p.WEB-DL" / f"Show.S0{season}E01.1080p.WEB-DL.mkv")
    return root / name


def paths(media_list) -> list[str]:
    return [os.path.relpath(media.subfolder, media.folder) for media in media_list]


def test_season_folders_of_a_series(tmp_path):
    show = series(tmp_path)
    assert Auto.season_folders(str(show)) == [str(show / "Show.S01.1080p.WEB-DL"), str(show / "Show.S02.1080p.WEB-DL")]


def test_season_folders_of_other_folders(tmp_path):
    # A season pack
    video(tmp_path / "Show.S01" / "Show.S01E01.mkv")
    assert Auto.season_folders(str(tmp_path / "Show.S01")) == []
    # Video files of its own: the subfolders are extras
    video(tmp_path / "Movie" / "Movie.mkv")
    video(tmp_path / "Movie" / "Extras.S01" / "Making.of.mkv")
    assert Auto.season_folders(str(tmp_path / "Movie")) == []
    # Subfolders with no season in the name, or with no video
    video(tmp_path / "Game" / "Movies" / "intro.mp4")
    (tmp_path / "Game" / "Show.S01").mkdir()
    assert Auto.season_folders(str(tmp_path / "Game")) == []


def test_scan_of_a_series_uploads_each_season(tmp_path):
    series(tmp_path)
    assert paths(Auto(path=str(tmp_path / SHOW), mode="auto").scan()) == [
        "Show.S01.1080p.WEB-DL", "Show.S02.1080p.WEB-DL"]


def test_scan_of_the_folder_of_the_series_uploads_each_season(tmp_path):
    """ -scan /tv: the series is split into its seasons, the other folders stay as they are (#116) """
    series(tmp_path)
    video(tmp_path / "Other.S03.720p" / "Other.S03E01.720p.mkv")
    video(tmp_path / "Movie.2020.mkv")
    assert paths(Auto(path=str(tmp_path), mode="auto").scan()) == [
        "Movie.2020.mkv",
        "Other.S03.720p",
        os.path.join(SHOW, "Show.S01.1080p.WEB-DL"),
        os.path.join(SHOW, "Show.S02.1080p.WEB-DL"),
    ]


def test_folder_mode_refuses_a_series_with_a_folder_for_each_season(tmp_path, capsys):
    """ -f uploads the files of the folder: with a folder for each season it stops with an error (#116) """
    show = series(tmp_path)
    assert Auto(path=str(show), mode="folder").upload() == []
    assert "upload one season at a time" in capsys.readouterr().out


def test_folder_mode_of_a_season_pack(tmp_path):
    video(tmp_path / "Show.S01" / "Show.S01E01.mkv")
    assert paths(Auto(path=str(tmp_path / "Show.S01"), mode="folder").upload()) == ["."]
