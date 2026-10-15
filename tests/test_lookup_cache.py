# -*- coding: utf-8 -*-
from types import SimpleNamespace

import pytest

from ittup.common import config_settings
from ittup.common.lookup_cache import LookupCache


@pytest.fixture
def cache_on(monkeypatch, tmp_path):
    monkeypatch.setattr(config_settings.user_preferences, "CACHE_DBONLINE", True)
    monkeypatch.setattr(config_settings.user_preferences, "CACHE_PATH", str(tmp_path))
    monkeypatch.setattr(LookupCache, "_cache", None)
    yield tmp_path
    if LookupCache._cache is not None:
        LookupCache._cache.close()
    LookupCache._cache = None


def test_off_by_default(monkeypatch):
    monkeypatch.setattr(config_settings.user_preferences, "CACHE_DBONLINE", False)
    LookupCache.set("tmdb", "x", value=[1])
    assert LookupCache.get("tmdb", "x") is None


def test_set_and_get(cache_on):
    LookupCache.set("tvdb", "tv", "Show", 2020, value={"result": {"tvdb_id": 1}})
    assert LookupCache.get("tvdb", "tv", "Show", 2020) == {"result": {"tvdb_id": 1}}
    assert LookupCache.get("tvdb", "movie", "Show", 2020) is None
    assert (cache_on / "lookups.cache").is_dir()


class FakeResponse:
    status_code = 200

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


def test_a_repeated_tmdb_request_is_read_from_the_cache(cache_on):
    from ittup.common.external_services.theMovieDB.core.api import TmdbAPI
    api = TmdbAPI.__new__(TmdbAPI)
    api.params = {"api_key": "secret", "language": "it-IT"}
    calls = []

    def get_url(url, params):
        calls.append((url, params))
        return FakeResponse({"results": [{"id": 1, "title": "Movie"}]})

    api.get_url = get_url
    endpoint = {"url": "https://api.themoviedb.org/3/search/movie", "datatype": dict, "query": "Movie",
                "results": "results"}
    assert api.request(endpoint) == [{"id": 1, "title": "Movie"}]
    assert api.request(endpoint) == [{"id": 1, "title": "Movie"}]
    assert len(calls) == 1
    # Another query is another request
    assert api.request({**endpoint, "query": "Other"}) == [{"id": 1, "title": "Movie"}]
    assert len(calls) == 2


def test_an_empty_tmdb_search_is_not_cached(cache_on):
    from ittup.common.external_services.theMovieDB.core.api import TmdbAPI
    api = TmdbAPI.__new__(TmdbAPI)
    api.params = {"api_key": "secret"}
    calls = []
    api.get_url = lambda url, params: calls.append(url) or FakeResponse({"results": []})
    endpoint = {"url": "https://api.themoviedb.org/3/search/movie", "datatype": dict, "query": "Movie",
                "results": "results"}
    assert api.request(endpoint) == [] and api.request(endpoint) == []
    assert len(calls) == 2


def test_a_repeated_tvdb_search_is_read_from_the_cache(cache_on):
    from ittup.common.external_services.tvdb import TVDB
    tvdb = TVDB.__new__(TVDB)
    tvdb.category = "tv"
    calls = []
    tvdb._search = lambda query, query_year: calls.append(query) or {"tvdb_id": 7, "imdb_id": "1"}
    assert tvdb.search("Show", 2020) == {"tvdb_id": 7, "imdb_id": "1"}
    assert tvdb.search("Show", 2020) == {"tvdb_id": 7, "imdb_id": "1"}
    assert calls == ["Show"]
