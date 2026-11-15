# -*- coding: utf-8 -*-
import argparse

from ittup.core.media_manager.ContentManager import ContentManager
from ittup.core.media_manager.VideoManager import VideoManager

SCENE_NFO = b"\xdb\xdb\xdb Movie.2020.1080p.BluRay.x264-GRP \xdb\xdb\xdb\r\n"
KODI_NFO = b'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n<movie><title>Movie</title></movie>\n'


def contents(path, mode="folder"):
    return ContentManager(path=str(path), mode=mode, cli=argparse.Namespace(force=None)).process()


def release(folder, video, nfo=None, content=SCENE_NFO):
    folder.mkdir()
    (folder / video).write_bytes(b"x")
    if nfo:
        (folder / nfo).write_bytes(content)
    return folder


def test_the_nfo_of_a_scene_movie(tmp_path):
    folder = release(tmp_path / "Movie.2020.1080p.BluRay.x264-GRP", "grp-movie-1080p.mkv", "grp-movie-1080p.nfo")

    media = contents(folder)[0]

    assert media.nfo == str(folder / "grp-movie-1080p.nfo")


def test_the_nfo_of_a_scene_season_pack(tmp_path):
    folder = release(tmp_path / "Show.S01.1080p.WEB.h264-GRP", "show.s01e01.1080p.web.h264-grp.mkv",
                     "show.s01.1080p.web.h264-grp.nfo")

    assert contents(folder)[0].nfo == str(folder / "show.s01.1080p.web.h264-grp.nfo")


def test_the_xml_nfo_of_kodi_and_radarr_is_not_the_release_nfo(tmp_path):
    folder = release(tmp_path / "Movie (2020)", "Movie (2020) 1080p.mkv", "movie.nfo", KODI_NFO)

    assert not contents(folder)[0].nfo
    assert not ContentManager.find_nfo(str(folder))


def test_the_xml_nfo_with_bom_is_skipped(tmp_path):
    (tmp_path / "tvshow.nfo").write_bytes(b"\xef\xbb\xbf\r\n" + KODI_NFO)

    assert ContentManager.find_nfo(str(tmp_path)) == ''


def test_the_release_nfo_next_to_a_kodi_nfo(tmp_path):
    (tmp_path / "movie.nfo").write_bytes(KODI_NFO)
    (tmp_path / "grp-movie.nfo").write_bytes(SCENE_NFO)

    assert ContentManager.find_nfo(str(tmp_path)) == str(tmp_path / "grp-movie.nfo")


def test_a_folder_named_nfo_is_skipped(tmp_path):
    (tmp_path / "Sample.nfo").mkdir()

    assert ContentManager.find_nfo(str(tmp_path)) == ''


def test_a_single_file_has_no_nfo(tmp_path):
    (tmp_path / "Movie.2020.1080p.BluRay.x264-GRP.mkv").write_bytes(b"x")
    (tmp_path / "Movie.2020.1080p.BluRay.x264-GRP.nfo").write_bytes(SCENE_NFO)

    assert not contents(tmp_path / "Movie.2020.1080p.BluRay.x264-GRP.mkv", mode="man")[0].nfo


def test_the_nfo_of_a_release_is_not_given_to_the_next_one(tmp_path):
    release(tmp_path / "A.Movie.2020.1080p.BluRay.x264-GRP", "a-movie.mkv", "a-movie.nfo")
    release(tmp_path / "B.Movie.2021.1080p.BluRay.x264-GRP", "b-movie.mkv")

    nfo = {media.torrent_name: media.nfo for media in contents(tmp_path, mode="auto")}

    assert nfo == {"A.Movie.2020.1080p.BluRay.x264-GRP": str(tmp_path / "A.Movie.2020.1080p.BluRay.x264-GRP"
                                                             / "a-movie.nfo"),
                   "B.Movie.2021.1080p.BluRay.x264-GRP": ''}


def test_the_nfo_follows_the_renamed_folder(tmp_path):
    folder = release(tmp_path / "movie.2020.1080p.bluray.x264-grp", "grp-movie.mkv", "grp-movie.nfo")
    media = contents(folder)[0]
    media.display_name = "Movie 2020 1080p BluRay x264"

    VideoManager.rename_files(media)

    assert media.nfo == str(tmp_path / "Movie.2020.1080p.BluRay.x264" / "grp-movie.nfo")
    assert (tmp_path / "Movie.2020.1080p.BluRay.x264" / "grp-movie.nfo").exists()
