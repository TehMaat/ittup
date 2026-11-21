# -*- coding: utf-8 -*-
"""The title of a game keeps the '-' before the releaser, as in the name of the release"""
import argparse
import os

import pytest

from ittup.common.utility import ManageTitles
from ittup.core import media as media_module
from ittup.core.media_manager.ContentManager import ContentManager


@pytest.mark.parametrize("release, title", [
    ("Black.Mesa.Anomalous.Improvements-RUNE", "Black Mesa Anomalous Improvements-RUNE"),
    ("STAR.WARS.Galactic.Racer-voices38", "STAR WARS Galactic Racer-voices38"),
    ("Some_Game_PC-TENOKE", "Some Game PC-TENOKE"),
    ("Some.Game.v1.2.3-FitGirl", "Some Game-FitGirl"),
    # Without a release group the title doesn't change
    ("Some Game PC", "Some Game PC"),
    ("Some.Game.[FitGirl.Repack]", "Some Game FitGirl Repack"),
])
def test_the_dash_before_the_releaser(release, title):
    display_name = ManageTitles.clean_text(release).replace("[", "").replace("]", "")
    assert ManageTitles.restore_releaser(display_name, release) == title


def test_a_group_missing_at_the_end_of_the_title_is_not_added():
    assert ManageTitles.restore_releaser("Some Game", "Some.Game-RUNE") == "Some Game"


class MediaFile:
    """MediaInfo of the test files: no video track"""

    def __init__(self, file_path: str):
        self.file_path = file_path

    video_track: list = []


@pytest.fixture(autouse=True)
def mediainfo(monkeypatch):
    monkeypatch.setattr(media_module, "MediaFile", MediaFile)


def display_name(path, force=None) -> str:
    [media] = ContentManager(path=str(path), mode="folder", cli=argparse.Namespace(force=force)).process()
    return media.display_name


def test_the_folder_of_a_game(tmp_path):
    folder = tmp_path / "Black.Mesa.Anomalous.Improvements-RUNE"
    folder.mkdir()
    (folder / "rune-bmai.iso").write_bytes(b"\x00" * 2048)
    assert display_name(folder) == "Black Mesa Anomalous Improvements-RUNE"


def test_the_iso_of_a_game(tmp_path):
    iso = tmp_path / "STAR.WARS.Galactic.Racer-voices38.iso"
    iso.write_bytes(b"\x00" * 2048)
    assert display_name(iso) == "STAR WARS Galactic Racer-voices38"


def test_a_document_is_not_changed(tmp_path):
    pdf = tmp_path / "Some.Magazine.2020-GRP.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    assert os.path.isfile(pdf)
    assert display_name(pdf) == "Some Magazine 2020 GRP"
