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
