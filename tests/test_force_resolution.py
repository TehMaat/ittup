# -*- coding: utf-8 -*-
import sys
from types import SimpleNamespace

import pytest

from ittup.common import tags
from ittup.common.command import CommandLine
from ittup.common.tags import SearchTags
from ittup.common.trackers.tags_list import TAGS_LIST
from ittup.common.trackers.trackers import TRACKData
from ittup.core import upload
from ittup.core.media import Media
from ittup.core.media_manager import VideoManager as video_manager
from ittup.core.media_manager.VideoManager import VideoManager
from ittup.core.upload import UploadBot

TAGS_POSITION = ["title", "year", "resolution", "uhd", "source", "vcodec"]


def parse(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["ittup", *args])
    return CommandLine().args


@pytest.mark.parametrize("args, expected", [
    (("-fres", "720p"), "720p"),
    (("-fres", "720P"), "720p"),
    (("--force-resolution", "Altro"), "altro"),
    ((), None),
])
def test_force_resolution_flag(monkeypatch, args, expected):
    assert parse(monkeypatch, "-u", "/tmp/movie.mkv", *args).force_resolution == expected


def test_force_resolution_flag_is_not_the_folder_flag(monkeypatch):
    args = parse(monkeypatch, "-f", "/tmp/folder", "-fres", "480p")
    assert args.folder == "/tmp/folder"
    assert args.force_resolution == "480p"


def test_a_resolution_unknown_to_the_tracker_is_refused(monkeypatch, capsys):
    with pytest.raises(SystemExit):
        parse(monkeypatch, "-u", "/tmp/movie.mkv", "-fres", "360p")
    error = capsys.readouterr().err
    assert "invalid resolution '360p'" in error
    assert "1080p" in error and "altro" in error


@pytest.fixture
def warnings(monkeypatch):
    logged = []
    monkeypatch.setattr(upload.custom_console, "bot_warning_log", logged.append)
    monkeypatch.setattr(upload.custom_console, "bot_error_log", logged.append)
    monkeypatch.setattr(upload.custom_console, "bot_log", lambda message: None)
    return logged


def resolution_id(resolution: str) -> int | None:
    bot = SimpleNamespace(content=SimpleNamespace(resolution=resolution),
                          tracker_data=TRACKData.load_from_module(tracker_name="ITT"))
    return UploadBot.resolution_id(bot)


@pytest.mark.parametrize("resolution, expected", [("2160p", 2), ("1080p", 3), ("720p", 5), ("480i", 9), ("altro", 10)])
def test_the_resolutions_of_the_tracker(warnings, resolution, expected):
    assert resolution_id(resolution) == expected
    assert not warnings


def test_a_resolution_unknown_to_the_tracker_is_sent_as_altro(warnings):
    assert resolution_id("360p") == 10
    assert warnings == ["Resolution '360p' unknown to the tracker: sent as 'altro', fix it on the tracker if needed"]


def test_without_altro_the_upload_stops(warnings):
    bot = SimpleNamespace(content=SimpleNamespace(resolution="360p"),
                          tracker_data=SimpleNamespace(resolution={"1080p": 3}))
    assert UploadBot.resolution_id(bot) is None


def title(resolution: str) -> tuple[str, dict]:
    mediafile = SimpleNamespace(general_track={}, video_track=[{"format": "AVC"}], audio_track=[],
                                subtitle_track=[])
    media = SimpleNamespace(mediafile=mediafile, torrent_pack=False, resolution=resolution, pack=None)
    search = SearchTags(filename="Movie.2020.WEB-DL.mkv", title="Movie", year="2020", season=None, episode=None,
                        media=media, tags_position=list(TAGS_POSITION), tags_list=TAGS_LIST, sign_list={},
                        ban_list={"dummy": "banned"}, releaser_sign="")
    return search.process()


@pytest.mark.parametrize("resolution, expected", [
    ("1080p", "Movie 2020 1080p FullHD WEB-DL H.264"),
    ("480p", "Movie 2020 480p SD WEB-DL H.264"),
    # MediaInfo without the width: the resolution is unknown, nothing is written
    ("altro", "Movie 2020 WEB-DL H.264"),
    # A resolution with no UHD/FullHD/HD/SD tag
    ("4320p", "Movie 2020 4320p WEB-DL H.264"),
])
def test_the_title_never_writes_unknown(monkeypatch, resolution, expected):
    monkeypatch.setattr(tags.custom_console, "bot_log", lambda message: None)
    built, _ = title(resolution)
    assert built == expected
    assert "unknown" not in built


def test_a_forced_resolution_is_not_read_from_mediainfo():
    media = Media.__new__(Media)
    media._resolution = None
    media.resolution = "720p"
    assert media.resolution == "720p"


def manager(contents: list, force_resolution: str | None) -> VideoManager:
    return VideoManager(contents=contents, cli=SimpleNamespace(force_resolution=force_resolution),
                        tags_list={}, sign_list={}, ban_list={})


def test_force_resolution_replaces_the_mediainfo_one(monkeypatch):
    logged = []
    monkeypatch.setattr(video_manager.custom_console, "bot_warning_log", logged.append)
    monkeypatch.setattr(video_manager.custom_console, "bot_log", lambda message: None)
    content = SimpleNamespace(resolution="1080p")
    manager([content], "720p").force_resolution(content)
    assert content.resolution == "720p"
    assert not logged


def test_force_resolution_on_a_folder_warns_once(monkeypatch):
    logged = []
    monkeypatch.setattr(video_manager.custom_console, "bot_warning_log", logged.append)
    monkeypatch.setattr(video_manager.custom_console, "bot_log", lambda message: None)
    contents = [SimpleNamespace(resolution="1080p"), SimpleNamespace(resolution="2160p")]
    videos = manager(contents, "altro")
    for content in contents:
        videos.force_resolution(content)
    assert [content.resolution for content in contents] == ["altro", "altro"]
    assert logged == ["-fres: 'altro' is the resolution of every file of this run"]


def test_without_force_resolution_nothing_changes():
    content = SimpleNamespace(resolution="1080p")
    VideoManager(contents=[content], cli=SimpleNamespace(), tags_list={}, sign_list={},
                 ban_list={}).force_resolution(content)
    assert content.resolution == "1080p"
