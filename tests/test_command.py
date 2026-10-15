# -*- coding: utf-8 -*-
import sys
from types import SimpleNamespace

import pytest

from ittup.common.command import CommandLine


def parse(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["ittup", *args])
    return CommandLine().args


@pytest.mark.parametrize("flag, percent", [("-fl25", 25), ("-fl50", 50), ("-fl75", 75), ("-fl100", 100),
                                           ("--freeleech50", 50)])
def test_freeleech_flags(monkeypatch, flag, percent):
    args = parse(monkeypatch, "-u", "/tmp/movie.mkv", flag)
    assert args.freeleech == percent
    assert args.upload == "/tmp/movie.mkv"


def test_no_freeleech(monkeypatch):
    assert parse(monkeypatch, "-f", "/tmp/folder").freeleech is None


def test_only_one_freeleech(monkeypatch):
    with pytest.raises(SystemExit):
        parse(monkeypatch, "-u", "/tmp/movie.mkv", "-fl25", "-fl50")


def test_freeleech_is_sent_to_the_tracker():
    from ittup.core.upload import UploadBot
    assert UploadBot.freeleech(SimpleNamespace(cli=SimpleNamespace(freeleech=75))) == 75
    assert UploadBot.freeleech(SimpleNamespace(cli=SimpleNamespace(freeleech=None))) == 0


def test_internal_flag(monkeypatch):
    assert parse(monkeypatch, "-u", "/tmp/movie.mkv", "-int", "-fl100").internal is True
    assert parse(monkeypatch, "-u", "/tmp/movie.mkv").internal is False


class FakeTracker:
    def __init__(self, data: dict, attributes: dict):
        self.data = data
        self.attributes = attributes
        self.fetched = []

    def fetch_id(self, torrent_id: int):
        self.fetched.append(torrent_id)
        return SimpleNamespace(json=lambda: {"data": {"id": str(torrent_id), "attributes": self.attributes}})


def check_flags(data: dict, attributes: dict, url="https://itatorrents.xyz/torrent/download/1234.abcdef"):
    from ittup.core.upload import UploadBot
    tracker = FakeTracker(data=data, attributes=attributes)
    bot = SimpleNamespace(tracker=tracker, tracker_name="ITT")
    warnings = []
    from ittup.core import upload
    original = upload.custom_console.bot_warning_log
    upload.custom_console.bot_warning_log = warnings.append
    try:
        UploadBot.check_flags(bot, download_url=url)
    finally:
        upload.custom_console.bot_warning_log = original
    return tracker.fetched, warnings


def test_flags_applied_by_the_tracker():
    fetched, warnings = check_flags({"internal": 1, "free": 100}, {"internal": 1, "freeleech": "100%"})
    assert fetched == [1234]
    assert warnings == []


def test_flags_ignored_by_the_tracker_are_reported():
    _, warnings = check_flags({"internal": 1, "free": 100}, {"internal": 0, "freeleech": "0%"})
    assert len(warnings) == 2
    assert warnings[0].startswith("-int:")
    assert warnings[1].startswith("-fl100:")


def test_no_flags_no_request():
    fetched, warnings = check_flags({"internal": 0, "free": 0}, {})
    assert fetched == [] and warnings == []


def test_internal_is_sent_for_every_category():
    from ittup.core.upload import UploadBot
    assert UploadBot.internal(SimpleNamespace(cli=SimpleNamespace(internal=True))) == 1
    assert UploadBot.internal(SimpleNamespace(cli=SimpleNamespace(internal=False))) == 0
