# -*- coding: utf-8 -*-
import os

from ittup.common.utility import System
from ittup.core.automode import Auto


def test_natural_key_sorts_numbers_by_value():
    names = ["Show E10.mkv", "show E2.mkv", "Show E1.mkv", "Alpha.mkv"]
    assert sorted(names, key=System.natural_key) == ["Alpha.mkv", "Show E1.mkv", "show E2.mkv", "Show E10.mkv"]


def test_scan_returns_files_and_folders_in_alphanumeric_order(tmp_path):
    for name in ["Zeta.2020.mkv", "beta.2020.mkv"]:
        (tmp_path / name).write_bytes(b"")
    for name in ["Movie 10", "Movie 2", "alpha"]:
        (tmp_path / name).mkdir()
        (tmp_path / name / "file.mkv").write_bytes(b"")

    titles = [media.title for media in Auto(path=str(tmp_path), mode="auto").scan()]
    assert titles == ["alpha", "beta.2020.mkv", "Movie 2", "Movie 10", "Zeta.2020.mkv"]


def test_upload_folder_files_in_alphanumeric_order(tmp_path):
    for name in ["E10.mkv", "E2.mkv", "E1.mkv"]:
        (tmp_path / name).write_bytes(b"")
    titles = [os.path.basename(media.title) for media in Auto(path=str(tmp_path), mode="man").upload()]
    assert titles == ["E1.mkv", "E2.mkv", "E10.mkv"]
