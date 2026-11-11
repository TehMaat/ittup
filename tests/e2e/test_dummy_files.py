# -*- coding: utf-8 -*-
"""
End-to-end tests: the ittup command on dummy video files made with ffmpeg

ITTup runs in a subprocess, with its own HOME and configuration, and the fake network of fake_network.py
in place of the tracker, TMDB, TVDB and the image hosts. The whole flow runs for real: guessit, MediaInfo,
the corrupted file check, the screenshots, the torrent file and the upload form sent to the tracker
"""
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(not (shutil.which("ffmpeg") and shutil.which("ffprobe")),
                                reason="the end-to-end tests need ffmpeg and ffprobe")

RUNNER = Path(__file__).parent / "run_ittup.py"
TIMEOUT = 300

MOVIE = "Dummy.Movie.2020.1080p.WEB-DL.AAC2.0.H.264.mkv"
SEASON = "Dummy.Show.S01.1080p.WEB-DL.AAC2.0.H.264"
# #114: the 'e7' in the group is not an episode
SEASON_GROUP = "Dummy.Show.S01.1080p.WEB-DL.AAC2.0.H.264-byMe7alh"


def dummy_video(path: Path, seconds: int) -> None:
    """
    A 1080p H.264 video with an Italian AAC stereo track
    A keyframe every second: the corrupted file check decodes a few frames near the end
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "testsrc2=size=1920x1080:rate=24",
                    "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000",
                    "-t", str(seconds), "-c:v", "libx264", "-preset", "ultrafast", "-crf", "40", "-g", "24",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-ac", "2", "-metadata:s:a:0", "language=ita",
                    str(path)], check=True)


@pytest.fixture(scope="module")
def media(tmp_path_factory) -> Path:
    folder = tmp_path_factory.mktemp("media")
    dummy_video(folder / MOVIE, seconds=20)
    for episode in (1, 2):
        dummy_video(folder / SEASON / f"Dummy.Show.S01E{episode:02d}.1080p.WEB-DL.AAC2.0.H.264.mkv", seconds=12)
        dummy_video(folder / SEASON_GROUP / f"Dummy.Show.S01E{episode:02d}.1080p.WEB-DL.AAC2.0.H.264.mkv", seconds=12)
    return folder


@pytest.fixture(scope="module")
def shows(tmp_path_factory) -> Path:
    """ For -scan: a folder with a season pack, and a show with a folder for each season """
    folder = tmp_path_factory.mktemp("shows")
    for episode in (1, 2):
        dummy_video(folder / "group" / SEASON_GROUP / f"Dummy.Show.S01E{episode:02d}.1080p.WEB-DL.AAC2.0.H.264.mkv",
                    seconds=12)
    for season in (1, 2):
        dummy_video(folder / "seasons" / f"Dummy.Show.S{season:02d}.1080p.WEB-DL.AAC2.0.H.264"
                    / f"Dummy.Show.S{season:02d}E01.1080p.WEB-DL.AAC2.0.H.264.mkv", seconds=12)
    return folder


@pytest.fixture
def home(tmp_path) -> Path:
    """ A HOME with the default configuration and the keys of the fake services """
    from ittup.common.settings import Load

    home = tmp_path / "home"
    config_path = home / "ittup_config" / "ittup.json"
    Load.create_default_json_file(config_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["tracker_config"].update(ITT_URL="https://tracker.test", ITT_APIKEY="e2e_key", ITT_PID="e2e_pid",
                                    TMDB_APIKEY="e2e_key", TVDB_APIKEY="e2e_key", PTSCREENS_KEY="e2e_key")
    config_path.write_text(json.dumps(config, indent=4), encoding="utf-8")
    return home


@dataclass
class Run:
    returncode: int
    output: str
    requests: list[dict]
    failures: list[str]
    archive: Path

    def uploads(self) -> list[dict]:
        """ The forms sent to the tracker upload API """
        return [r["form"] for r in self.requests
                if r["method"] == "POST" and r["url"] == "https://tracker.test/api/torrents/upload"]

    def torrents(self) -> list[str]:
        return sorted(path.name for path in self.archive.rglob("*.torrent"))


def ittup(home: Path, *arguments: str) -> Run:
    requests_log = home / "requests.jsonl"
    report_file = home / "report.json"
    env = {**os.environ, "HOME": str(home), "LOCALAPPDATA": str(home), "COLUMNS": "200",
           "ITTUP_E2E_REQUESTS": str(requests_log), "ITTUP_E2E_REPORT": str(report_file)}
    # stdin closed: a question to the user ends the run instead of waiting forever
    result = subprocess.run([sys.executable, str(RUNNER), *arguments], cwd=home, env=env,
                            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=TIMEOUT)
    output = result.stdout + result.stderr
    print(output)
    requests = [json.loads(line) for line in requests_log.read_text(encoding="utf-8").splitlines()] \
        if requests_log.exists() else []
    failures = json.loads(report_file.read_text(encoding="utf-8")) if report_file.exists() else []
    return Run(returncode=result.returncode, output=output, requests=requests, failures=failures,
               archive=home / "ittup_config" / "torrent_archive_path")


def assert_clean(run: Run) -> None:
    """ No crash, no skipped content and no request to a service unknown to the fake network """
    assert run.returncode == 0, run.output
    assert "Traceback" not in run.output, run.output
    assert run.failures == []
    assert [r["url"] for r in run.requests if r["unmatched"]] == []


def test_upload_a_movie(home, media):
    run = ittup(home, "-u", str(media / MOVIE), "-noseed")

    assert_clean(run)
    assert run.torrents() == [f"{MOVIE}.torrent"]
    [upload] = run.uploads()
    assert upload["name"] == "Film Finto 2020 1080p FullHD WEB-DL AAC 2.0 ITA SDR H.264"
    assert upload["category_id"] == "1"
    assert upload["tmdb"] == "550"
    assert upload["imdb"] == "137523"
    assert "https://ptscreens.com/images/dummy.png" in upload["description"]


def test_noup_creates_the_torrent_without_uploading(home, media):
    run = ittup(home, "-u", str(media / MOVIE), "-noup")

    assert_clean(run)
    assert run.torrents() == [f"{MOVIE}.torrent"]
    assert run.uploads() == []


def test_upload_the_episodes_of_a_folder(home, media):
    run = ittup(home, "-u", str(media / SEASON), "-noseed")

    assert_clean(run)
    assert [(u["name"], u["season_number"], u["episode_number"]) for u in run.uploads()] == [
        ("Serie Finta S01E01 1080p FullHD WEB-DL AAC 2.0 ITA SDR H.264", "1", "1"),
        ("Serie Finta S01E02 1080p FullHD WEB-DL AAC 2.0 ITA SDR H.264", "1", "2"),
    ]
    assert all(u["category_id"] == "2" and u["tmdb"] == "1399" for u in run.uploads())


def test_upload_a_season_pack(home, media):
    run = ittup(home, "-f", str(media / SEASON), "-noseed")

    assert_clean(run)
    assert run.torrents() == [f"{SEASON}.torrent"]
    [upload] = run.uploads()
    assert upload["name"] == "Serie Finta S01 1080p FullHD WEB-DL AAC 2.0 ITA SDR H.264"
    assert (upload["season_number"], upload["episode_number"]) == ("1", "0")


def test_upload_a_season_pack_with_an_e_and_a_number_in_the_group(home, media):
    run = ittup(home, "-f", str(media / SEASON_GROUP), "-noseed")

    assert_clean(run)
    assert run.torrents() == [f"{SEASON_GROUP}.torrent"]
    [upload] = run.uploads()
    assert (upload["season_number"], upload["episode_number"]) == ("1", "0")


def test_scan_uploads_a_season_pack_with_an_e_and_a_number_in_the_group(home, shows):
    run = ittup(home, "-scan", str(shows / "group"), "-noseed")

    assert_clean(run)
    assert run.torrents() == [f"{SEASON_GROUP}.torrent"]
    [upload] = run.uploads()
    assert (upload["season_number"], upload["episode_number"]) == ("1", "0")


def test_scan_uploads_a_pack_for_each_season_folder(home, shows):
    run = ittup(home, "-scan", str(shows / "seasons"), "-noseed")

    assert_clean(run)
    assert run.torrents() == ["Dummy.Show.S01.1080p.WEB-DL.AAC2.0.H.264.torrent",
                              "Dummy.Show.S02.1080p.WEB-DL.AAC2.0.H.264.torrent"]
    assert [(u["name"], u["season_number"], u["episode_number"]) for u in run.uploads()] == [
        ("Serie Finta S01 1080p FullHD WEB-DL AAC 2.0 ITA SDR H.264", "1", "0"),
        ("Serie Finta S02 1080p FullHD WEB-DL AAC 2.0 ITA SDR H.264", "2", "0"),
    ]
