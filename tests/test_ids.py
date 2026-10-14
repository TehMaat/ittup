# -*- coding: utf-8 -*-
from types import SimpleNamespace

import pytest

from ittup.core.media_manager.ContentManager import ContentManager


def search_ids(file_name: str, display_name: str) -> SimpleNamespace:
    manager = SimpleNamespace(file_name=file_name, display_name=display_name)
    ContentManager.search_ids(manager)
    return manager


@pytest.mark.parametrize("name, field, value", [
    ("The Matrix (1999) {tmdb-603}.mkv", "tmdb_id", "603"),
    ("The Matrix (1999) {imdb-tt0133093}.mkv", "imdb_id", "0133093"),
    ("The Matrix (1999) [tmdbid-603].mkv", "tmdb_id", "603"),
    ("The Matrix (1999) [tmdbid=603].mkv", "tmdb_id", "603"),
    ("The Matrix (1999) (tmdb-603).mkv", "tmdb_id", "603"),
    ("The.Matrix.1999.tmdb-603.1080p.mkv", "tmdb_id", "603"),
    ("The Matrix (1999) [imdbid-tt0133093].mkv", "imdb_id", "0133093"),
    ("The.Matrix.1999.tt0133093.1080p.mkv", "imdb_id", "0133093"),
    ("Show (2020) {tvdb-12345} S01.mkv", "tvdb_id", "12345"),
])
def test_ids_in_the_name(name, field, value):
    assert getattr(search_ids(name, name), field) == value


def test_no_id_in_the_name():
    manager = search_ids("/upload/The Matrix (1999) 1080p.mkv", "The Matrix 1999 1080p")
    assert (manager.tmdb_id, manager.imdb_id, manager.tvdb_id) == (0, 0, 0)
    assert manager.display_name == "The Matrix 1999 1080p"


def test_the_id_is_removed_from_the_display_name():
    assert search_ids("The Matrix (1999) [tmdbid-603].mkv", "The Matrix 1999 tmdbid 603 1080p").display_name == \
        "The Matrix 1999 1080p"
    assert search_ids("The Matrix (1999) {tmdb-603}.mkv", "The Matrix 1999 {tmdb 603} 1080p").display_name == \
        "The Matrix 1999 1080p"
    assert search_ids("The.Matrix.1999.tt0133093.mkv", "The Matrix 1999 tt0133093 1080p").display_name == \
        "The Matrix 1999 1080p"
