# -*- coding: utf-8 -*-
import json
from types import SimpleNamespace

import pytest

from ittup.core.report import report, TemporaryFailure
from ittup.core import upload
from ittup.core.upload import UploadBot


def bot() -> UploadBot:
    upload_bot = UploadBot.__new__(UploadBot)
    upload_bot.tracker_name = "ITT"
    upload_bot.content = SimpleNamespace(file_name="/movies/Movie.mkv", display_name="Movie 2020 1080p")
    upload_bot.tracker = SimpleNamespace(data={"internal": 0, "free": 0})
    return upload_bot


def response(status_code: int, body) -> SimpleNamespace:
    return SimpleNamespace(status_code=status_code, text=body if isinstance(body, str) else json.dumps(body))


@pytest.mark.parametrize("status_code, body", [
    (500, {"message": "Server Error"}),
    (502, "<html>Bad Gateway</html>"),
    (503, "<html>Service Unavailable</html>"),
    (429, {"message": "Too Many Attempts."}),
])
def test_tracker_errors_that_go_away_are_temporary(status_code, body):
    with pytest.raises(TemporaryFailure):
        bot().message(response(status_code, body), torrent_archive="/archive/Movie.torrent")


def test_a_refused_upload_is_a_failure_of_the_report():
    report.reset()
    upload_bot = bot()
    upload_bot.tracker.upload_t = lambda **kwargs: response(
        422, {"success": False, "data": {"name": ["The name has already been taken."]}})
    assert upload_bot.send(torrent_archive="/archive/Movie.torrent")[0] == {}
    assert report.failures == ["'Movie 2020 1080p': upload refused by the tracker: UploadBot - "
                               "The name has already been taken. : "]
    report.reset()


FAKE_REMUX = "possible fake REMUX: video encoded with x264 core 164 r3095 baee400"


@pytest.fixture
def logged(monkeypatch):
    messages = []
    monkeypatch.setattr(upload.custom_console, "bot_warning_log", messages.append)
    monkeypatch.setattr(upload.config_settings.user_preferences, "AUTO_MODERATION", True)
    monkeypatch.setattr(upload.config_settings.user_preferences, "PERSONAL_RELEASE", False)
    return messages


def video_upload(review_reasons: list[str], moderation: bool = False) -> dict:
    """ The data of a video upload, as sent to the tracker """
    upload_bot = UploadBot.__new__(UploadBot)
    upload_bot.cli = SimpleNamespace(moderation=moderation, personal=False, internal=False, freeleech=None)
    upload_bot.sign = "[sign]"
    upload_bot.content = SimpleNamespace(
        display_name="Movie 2020 1080p BluRay REMUX AVC-GRP", category="movie", resolution="1080p",
        mediainfo_source=None, torrent_name="Movie.2020.1080p.BluRay.REMUX.AVC-GRP",
        file_name="Movie.2020.1080p.BluRay.REMUX.AVC-GRP.mkv", guess_season=None, guess_episode=None,
        torrent_pack=False, review_reasons=review_reasons)
    upload_bot.tracker_data = SimpleNamespace(category={"movie": 1}, resolution={"1080p": 3},
                                              filter_type=lambda *names: 42)
    upload_bot.tracker = SimpleNamespace(data={})
    video_info = SimpleNamespace(mediainfo="mediainfo", description="[screenshots]", is_hd=0)
    return upload_bot.data(show_id=1, imdb_id=2, tvdb_id=0, show_keywords_list="", video_info=video_info).data


@pytest.mark.parametrize("reason", [FAKE_REMUX, "possible WEBRip: x264 crf=21.0, no VBV"])
def test_a_suspicious_file_is_sent_to_moderation(logged, reason):
    data = video_upload([reason])
    assert data["mod_queue_opt_in"] == 1
    assert logged == [f"Sent to moderation: {reason}"]
    # The staff decides: the title, the type and the public description don't change
    assert data["name"] == "Movie 2020 1080p BluRay REMUX AVC-GRP"
    assert data["type_id"] == 42
    assert data["description"] == "[screenshots][sign]"


@pytest.mark.parametrize("moderation", [False, True])
def test_without_reasons_only_the_flag_asks_for_moderation(logged, moderation):
    assert video_upload([], moderation=moderation)["mod_queue_opt_in"] == int(moderation)
    assert not logged


@pytest.mark.parametrize("moderation", [False, True])
def test_auto_moderation_off_leaves_only_the_warning(logged, monkeypatch, moderation):
    monkeypatch.setattr(upload.config_settings.user_preferences, "AUTO_MODERATION", False)
    assert video_upload([FAKE_REMUX], moderation=moderation)["mod_queue_opt_in"] == int(moderation)
    assert not logged


def test_a_content_without_review_reasons():
    # A content that didn't go through SearchTags
    upload_bot = SimpleNamespace(cli=SimpleNamespace(moderation=False), content=SimpleNamespace())
    assert UploadBot.moderation(upload_bot) == 0
