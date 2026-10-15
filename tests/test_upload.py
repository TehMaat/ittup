# -*- coding: utf-8 -*-
import json
from types import SimpleNamespace

import pytest

from ittup.core.report import report, TemporaryFailure
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
