# -*- coding: utf-8 -*-
from types import SimpleNamespace

import pytest

from ittup.common.external_services.theMovieDB.core.api import DbOnline


@pytest.mark.parametrize("query, name, queries", [
    ("Days of Summer", "(500) Days of Summer (2009) 1080p BluRay x264.mkv", ["Days of Summer", "500 Days of Summer"]),
    ("Lo Chiamavano Jeeg Robot", "Lo Chiamavano Jeeg Robot (They Call Me Jeeg) (2015) 1080p.mkv",
     ["Lo Chiamavano Jeeg Robot", "Lo Chiamavano Jeeg Robot They Call Me Jeeg", "They Call Me Jeeg"]),
    ("The Matrix", "The.Matrix.1999.1080p.BluRay.x264.mkv", ["The Matrix"]),
    ("Mare Fuori", "Mare Fuori S04E01 1080p.mkv", ["Mare Fuori"]),
    ("SWAT", "S.W.A.T.2017.S01.1080p", ["SWAT", "S.W.A.T"]),
])
def test_title_queries(query, name, queries):
    assert DbOnline.title_queries(query, name) == queries


class Result(SimpleNamespace):
    def get_date(self):
        return self.date


def year_matches(category: str, file_year: int, tmdb_date: str, relaxed: bool) -> bool:
    media = SimpleNamespace(guess_filename=SimpleNamespace(guessit_year=file_year))
    db = SimpleNamespace(media=media, category=category, relaxed_year=relaxed)
    return DbOnline.year_matches(db, Result(date=tmdb_date))


def test_exact_year_first():
    assert year_matches("movie", 2023, "2023-12-20", relaxed=False)
    assert not year_matches("movie", 2024, "2023-12-20", relaxed=False)


def test_year_tolerance():
    # Movie released at the end of the year, in Italy the next one
    assert year_matches("movie", 2024, "2023-12-20", relaxed=True)
    assert not year_matches("movie", 2026, "2023-12-20", relaxed=True)
    # The year of a later season
    assert year_matches("tv", 2024, "2020-09-23", relaxed=True)
    assert not year_matches("tv", 2005, "2020-09-23", relaxed=True)


class Movie(SimpleNamespace):
    def get_date(self):
        return self.date

    def get_title(self):
        return self.title

    def get_original(self):
        return self.title


def db_online(query: str, name: str, year: int | None, tmdb: dict) -> DbOnline:
    db = DbOnline.__new__(DbOnline)
    db.media = SimpleNamespace(title=name, guess_filename=SimpleNamespace(guessit_year=year))
    db.query, db.category, db.no_title, db.relaxed_year = query, "movie", None, False
    db._search = lambda q, category: tmdb.get(q, [])
    db.alternative = lambda media_id, category: []
    db.translations = lambda media_id, category: []
    return db


def test_search_with_the_title_in_parentheses(monkeypatch):
    summer = Movie(id=19913, title="(500) Days of Summer", date="2009-07-17")
    db = db_online("Days of Summer", "(500) Days of Summer (2009) 1080p.mkv", 2009, {"500 Days of Summer": [summer]})
    result, _ = db.search_queries()
    assert result is summer
    assert db.query == "500 Days of Summer"


def test_search_with_a_year_tolerance():
    movie = Movie(id=1, title="Povere creature!", date="2023-12-08")
    other = Movie(id=2, title="Povere creature!", date="1990-01-01")
    db = db_online("Povere creature!", "Povere creature! 2024 1080p.mkv", 2024, {"Povere creature!": [other, movie]})
    result, _ = db.search_queries()
    assert result is movie
    assert db.relaxed_year is False


def test_search_not_found_keeps_the_first_query():
    db = db_online("Nothing", "Nothing (Niente) 2020.mkv", 2020, {})
    assert db.search_queries() == (None, [])
    assert db.query == "Nothing"
