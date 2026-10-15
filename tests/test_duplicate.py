# -*- coding: utf-8 -*-
from types import SimpleNamespace

import pytest

from ittup.common import title
from ittup.core.duplicate import Duplicate

RESOLUTIONS = {"2160p": 2, "1080p": 3, "720p": 5}
GB = 1024 ** 3


class FakeTorrent:
    """ Torrent with the answers of the tracker: by name and by TMDB ID """

    def __init__(self, by_name: list, by_tmdb: list):
        self.tracker = SimpleNamespace(params={"stale": "filter"})
        self.by_name, self.by_tmdb = by_name, by_tmdb
        self.calls = []

    def search(self, keyword: str) -> dict:
        self.calls.append(("name", keyword, dict(self.tracker.params)))
        return {"data": self.by_name}

    def get_by_tmdb_id(self, tmdb_id: int) -> dict:
        self.calls.append(("tmdb", tmdb_id, dict(self.tracker.params)))
        return {"data": self.by_tmdb}


def torrent(torrent_id: int, name: str, size_gb: float, resolution_id: int = 3, category_id: int = 1,
            tmdb_id: int = 0) -> dict:
    return {"id": str(torrent_id), "attributes": {"name": name, "size": int(size_gb * GB), "resolution_id": resolution_id,
                                                   "category_id": category_id, "tmdb_id": tmdb_id}}


def duplicate(display_name: str, torrent_info: FakeTorrent, category="movie", tmdb_id=0, resolution="1080p",
              pack=None, size_gb=10.0) -> Duplicate:
    dup = Duplicate.__new__(Duplicate)
    dup.content = SimpleNamespace(display_name=display_name, resolution=resolution, pack=pack)
    dup.tmdb_id = tmdb_id
    dup.cli = SimpleNamespace(notitle=None)
    dup.torrent_info = torrent_info
    dup.resolutions = RESOLUTIONS
    dup.category = category
    dup.category_id = {"movie": 1, "tv": 2}[category]
    dup.guess_filename = title.Guessit(display_name)
    dup.query = dup.guess_filename
    dup.content_size, dup.size_unit = size_gb, "GB"
    dup.size_threshold = 10
    dup._print_output = lambda **kwargs: None
    return dup


@pytest.fixture(autouse=True)
def config(monkeypatch):
    from ittup.core import duplicate as module
    preferences = SimpleNamespace(SIZE_TH=10, SKIP_DUPLICATE=True)
    monkeypatch.setattr(module, "config_settings", SimpleNamespace(user_preferences=preferences))


def test_search_by_title_and_by_tmdb_id():
    fake = FakeTorrent(by_name=[torrent(1, "Movie 2020 1080p", 10)],
                       by_tmdb=[torrent(1, "Movie 2020 1080p", 10), torrent(2, "Il Film 2020 1080p", 10)])
    dup = duplicate("Movie 2020 1080p WEB-DL", fake, tmdb_id=123)
    assert [t["id"] for t in dup.tracker_results()] == ["1", "2"]
    # Each search starts without the filters of the previous one, the ID search only in the same category
    assert fake.calls == [("name", "Movie", {}), ("tmdb", 123, {"categories[]": 1})]


def test_the_same_tmdb_id_is_a_duplicate_whatever_the_title():
    fake = FakeTorrent(by_name=[], by_tmdb=[torrent(2, "Il Film Italiano 2020 1080p", 10.5, tmdb_id=123)])
    assert duplicate("Movie 2020 1080p WEB-DL", fake, tmdb_id=123).process() is True


def test_a_different_resolution_is_not_a_duplicate():
    fake = FakeTorrent(by_name=[torrent(1, "Movie 2020 720p", 10, resolution_id=5)], by_tmdb=[])
    assert duplicate("Movie 2020 1080p WEB-DL", fake).process() is False


def test_a_different_category_is_not_a_duplicate():
    fake = FakeTorrent(by_name=[torrent(1, "Movie 2020 1080p", 10, category_id=2)], by_tmdb=[])
    assert duplicate("Movie 2020 1080p WEB-DL", fake).process() is False


def test_same_title_and_size_is_a_duplicate():
    fake = FakeTorrent(by_name=[torrent(1, "Movie 2020 1080p BluRay", 10.2)], by_tmdb=[])
    assert duplicate("Movie 2020 1080p WEB-DL", fake).process() is True


def test_a_size_out_of_the_threshold_is_not_a_duplicate():
    fake = FakeTorrent(by_name=[torrent(1, "Movie 2020 1080p", 4)], by_tmdb=[])
    assert duplicate("Movie 2020 1080p WEB-DL", fake).process() is False


def test_another_episode_of_the_same_show_is_not_a_duplicate():
    fake = FakeTorrent(by_name=[], by_tmdb=[torrent(1, "Show S01E02 1080p", 1, category_id=2, tmdb_id=9)])
    assert duplicate("Show S01E01 1080p WEB-DL", fake, category="tv", tmdb_id=9, size_gb=1).process() is False
    fake = FakeTorrent(by_name=[], by_tmdb=[torrent(1, "Show S01E01 1080p", 1, category_id=2, tmdb_id=9)])
    assert duplicate("Show S01E01 1080p WEB-DL", fake, category="tv", tmdb_id=9, size_gb=1).process() is True


def test_empty_sizes():
    dup = duplicate("Movie 2020 1080p", FakeTorrent([], []), size_gb=0)
    assert dup._calculate_threshold(0) == 0
