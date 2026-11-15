# -*- coding: utf-8 -*-
import os

import pytest

from ittup.common.utility import System

MB = 1024 ** 2

symlinks = pytest.mark.skipif(not hasattr(os, "symlink") or os.name == "nt",
                              reason="symlinks need privileges on Windows")


def test_folder_size_sums_the_files(tmp_path):
    (tmp_path / "E01.mkv").write_bytes(b"\0" * 3 * MB)
    (tmp_path / "E02.mkv").write_bytes(b"\0" * 2 * MB)
    assert System.get_size(str(tmp_path)) == (5.0, "MB")


@symlinks
def test_folder_size_follows_symlinked_files(tmp_path):
    library = tmp_path / "library"
    library.mkdir()
    (library / "E01.mkv").write_bytes(b"\0" * 3 * MB)
    (library / "E02.mkv").write_bytes(b"\0" * 2 * MB)
    season = tmp_path / "seed" / "Show.S01"
    season.mkdir(parents=True)
    for name in ["E01.mkv", "E02.mkv"]:
        os.symlink(library / name, season / name)

    assert System.get_size(str(season)) == (5.0, "MB")


@symlinks
def test_folder_size_follows_symlinked_folders_and_skips_broken_links(tmp_path):
    library = tmp_path / "library" / "Extras"
    library.mkdir(parents=True)
    (library / "Extra.mkv").write_bytes(b"\0" * 2 * MB)
    release = tmp_path / "Show.S01"
    release.mkdir()
    (release / "E01.mkv").write_bytes(b"\0" * 1 * MB)
    os.symlink(library, release / "Extras")
    os.symlink(tmp_path / "missing.mkv", release / "E02.mkv")

    assert System.get_size(str(release)) == (3.0, "MB")


@symlinks
def test_single_symlinked_file_size(tmp_path):
    (tmp_path / "Movie.mkv").write_bytes(b"\0" * 4 * MB)
    os.symlink(tmp_path / "Movie.mkv", tmp_path / "link.mkv")
    assert System.get_size(str(tmp_path / "link.mkv")) == (4.0, "MB")
