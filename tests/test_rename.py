# -*- coding: utf-8 -*-
import argparse

import pytest

from ittup.common.rename import is_valid_name, rename_invalid, safe_name
from ittup.core.media_manager.ContentManager import ContentManager


@pytest.mark.parametrize("name, safe", [
    ("Mission: Impossible - Dead Reckoning 2023 1080p.mkv", "Mission - Impossible - Dead Reckoning 2023 1080p.mkv"),
    ("Titolo: Sub 2023", "Titolo - Sub 2023"),
    ("Mission:Impossible.2023.1080p.mkv", "Mission.Impossible.2023.1080p.mkv"),
    ("Che cosa? 2020 1080p.mkv", "Che cosa 2020 1080p.mkv"),
    ('Il "film" * 2020.mkv', "Il film 2020.mkv"),
    ("Cartella finita con il punto.", "Cartella finita con il punto"),
    ("Mr. Robot S01", "Mr. Robot S01"),
    # Dash and exclamation mark are valid
    ("Ciao! Spider-Man 2020.mkv", "Ciao! Spider-Man 2020.mkv"),
])
def test_safe_name(name, safe):
    assert safe_name(name) == safe
    assert is_valid_name(safe)


def test_rename_a_folder_and_its_files(tmp_path):
    folder = tmp_path / "Show: The Series S01 1080p"
    (folder / "Extras?").mkdir(parents=True)
    (folder / "Show: The Series S01E01.mkv").write_bytes(b"1")
    (folder / "Extras?" / "Making of: part 1.mkv").write_bytes(b"2")
    (folder / "Valid S01E02.mkv").write_bytes(b"3")

    new_path = rename_invalid(str(folder))

    renamed = tmp_path / "Show - The Series S01 1080p"
    assert new_path == str(renamed)
    assert sorted(p.relative_to(renamed).as_posix() for p in renamed.rglob("*")) == [
        "Extras", "Extras/Making of - part 1.mkv", "Show - The Series S01E01.mkv", "Valid S01E02.mkv"]


def test_a_valid_file_is_not_renamed(tmp_path):
    movie = tmp_path / "Movie 2020 1080p.mkv"
    movie.write_bytes(b"")
    assert rename_invalid(str(movie)) == str(movie)
    assert movie.exists()


def test_content_manager_uses_the_renamed_folder(tmp_path):
    folder = tmp_path / "Movie: Part 2020 1080p WEB-DL"
    folder.mkdir()
    (folder / "Movie: Part 2020 1080p WEB-DL.mkv").write_bytes(b"x")
    cli = argparse.Namespace(force=None)

    contents = ContentManager(path=str(folder), mode="folder", cli=cli).process()

    assert len(contents) == 1
    media = contents[0]
    renamed = tmp_path / "Movie - Part 2020 1080p WEB-DL"
    assert media.torrent_path == str(renamed)
    assert media.torrent_name == "Movie - Part 2020 1080p WEB-DL"
    assert media.file_name == str(renamed / "Movie - Part 2020 1080p WEB-DL.mkv")
    assert '"Movie - Part 2020 1080p WEB-DL.mkv"' in media.metainfo
