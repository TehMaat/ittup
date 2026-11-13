# -*- coding: utf-8 -*-
import json
from types import SimpleNamespace

import pytest

from ittup.common import config_settings
from ittup.common.external_services.theMovieDB.core import api
from ittup.common.external_services.theMovieDB.core.api import DbOnline
from ittup.common.manual_ids import ManualIds
from ittup.view import custom_console


@pytest.fixture
def ids(tmp_path):
    return ManualIds(tmp_path / "manual_ids.json")


def test_saved_id_is_found_again(ids):
    ids.set("tv", "Bake Off Italia", None, 12345, "Bake Off Italia - Dolci in forno")
    assert ids.get("tv", "Bake.Off.Italia", None) == 12345
    saved = json.loads(ids.path.read_text(encoding="utf-8"))
    assert saved["tv|bake off italia|"]["tmdb_id"] == 12345
    assert saved["tv|bake off italia|"]["title"] == "Bake Off Italia - Dolci in forno"


def test_skip_is_not_saved(ids):
    ids.set("movie", "Nothing", 2020, 0)
    assert not ids.path.exists()


def test_movie_needs_the_same_year_and_category(ids):
    ids.set("movie", "Titolo", 2019, 67890)
    assert ids.get("movie", "Titolo", 2019) == 67890
    assert ids.get("movie", "Titolo", 2020) is None
    assert ids.get("movie", "Titolo", None) is None
    assert ids.get("tv", "Titolo", 2019) is None


def test_tv_show_matches_with_or_without_the_year(ids):
    ids.set("tv", "Serie", None, 1)
    assert ids.get("tv", "Serie", 2024) == 1
    ids.set("tv", "Altra Serie", 2024, 2)
    assert ids.get("tv", "Altra Serie", None) == 2


def test_tv_show_saved_with_two_years_is_ambiguous(ids):
    ids.set("tv", "Serie", 2005, 1)
    ids.set("tv", "Serie", 2020, 2)
    assert ids.get("tv", "Serie", None) is None
    assert ids.get("tv", "Serie", 2020) == 2


def test_corrupt_file_is_kept_and_replaced_on_save(ids):
    ids.path.write_text("{not json", encoding="utf-8")
    assert ids.get("tv", "Serie", None) is None
    # Reading doesn't touch the file
    assert ids.path.read_text(encoding="utf-8") == "{not json"
    ids.set("tv", "Serie", None, 7)
    assert ids.get("tv", "Serie", None) == 7
    assert ids.path.with_name("manual_ids.json.bad").read_text(encoding="utf-8") == "{not json"


def test_entry_edited_by_hand_is_ignored(ids):
    ids.path.write_text(json.dumps({"tv|serie|": {"tmdb_id": "abc"}, "tv|altra|": 5}), encoding="utf-8")
    assert ids.get("tv", "Serie", None) is None
    assert ids.get("tv", "Altra", None) == 5


class Show(SimpleNamespace):
    def get_title(self):
        return self.title

    def get_date(self):
        return "2013-01-01"


def db_online(query: str, year: int | None, known: dict) -> DbOnline:
    """ A DbOnline where TMDB never finds the title by name and knows only the IDs in 'known' """
    db = DbOnline.__new__(DbOnline)
    db.media = SimpleNamespace(guess_filename=SimpleNamespace(guessit_year=year), guess_season=1, guess_episode=1,
                               torrent_pack=False)
    db.query, db.category, db.no_title, db.relaxed_year = query, "tv", None, False
    db.imdb_id = db.tvdb_id = None
    db.search_queries = lambda: (None, [])
    db.tvdb_search = lambda: None
    db.search_id = lambda video_id: known.get(video_id)
    db.external_ids = lambda video_id, category: {}
    db.trailer = lambda video_id: "not available"
    db.keywords = lambda video_id: ""
    db.youtube_trailer = lambda: "not available"
    return db


@pytest.fixture
def tmdb(tmp_path, monkeypatch):
    """ Saved IDs in a temporary file, no cache, the typed IDs counted """
    monkeypatch.setattr(api, "MANUAL_IDS_PATH", tmp_path / "manual_ids.json")
    monkeypatch.setattr(config_settings.user_preferences, "CACHE_DBONLINE", False)
    monkeypatch.setattr(config_settings.user_preferences, "SKIP_TMDB", False)
    typed = []

    def user_input(message):
        typed.append(message)
        return typed_ids.pop(0)

    typed_ids = []
    monkeypatch.setattr(custom_console, "user_input", user_input)
    return SimpleNamespace(typed=typed, typed_ids=typed_ids, path=tmp_path / "manual_ids.json")


def test_id_is_asked_once_for_two_episodes(tmdb):
    known = {12345: Show(title="Bake Off Italia - Dolci in forno")}
    tmdb.typed_ids.append(12345)
    first = db_online("Bake Off Italia", None, known).search()
    second = db_online("Bake Off Italia", None, known).search()
    assert first.video_id == second.video_id == 12345
    assert len(tmdb.typed) == 1


def test_skip_is_asked_again(tmdb):
    tmdb.typed_ids.extend([0, 0])
    assert db_online("Nothing", None, {}).search().video_id == 0
    assert db_online("Nothing", None, {}).search().video_id == 0
    assert len(tmdb.typed) == 2
    assert not tmdb.path.exists()


def test_saved_id_is_used_with_skip_tmdb(tmdb, monkeypatch):
    ManualIds(tmdb.path).set("tv", "Bake Off Italia", None, 12345)
    monkeypatch.setattr(config_settings.user_preferences, "SKIP_TMDB", True)
    result = db_online("Bake Off Italia", None, {12345: Show(title="Bake Off")}).search()
    assert result.video_id == 12345
    assert not tmdb.typed


def test_saved_id_no_longer_valid_is_asked_again(tmdb):
    ManualIds(tmdb.path).set("tv", "Serie", None, 999)
    tmdb.typed_ids.append(5)
    result = db_online("Serie", None, {5: Show(title="Serie")}).search()
    assert result.video_id == 5
    assert ManualIds(tmdb.path).get("tv", "Serie", None) == 5


def test_id_in_the_file_name_wins_over_the_saved_one(tmdb, monkeypatch):
    ManualIds(tmdb.path).set("tv", "Serie", None, 999)
    db = db_online("Serie", None, {})
    used = []
    monkeypatch.setattr(db, "search", lambda: used.append("saved"), raising=False)
    monkeypatch.setattr(db, "results_in_string", lambda tmdb_id, imdb_id, tvdb_id: tmdb_id)
    media = SimpleNamespace(tmdb_id="42", imdb_id=None, tvdb_id=None, guess_title="Serie")
    monkeypatch.setattr(api.TmdbAPI, "__init__", lambda self: None)
    db.__init__(media=media, category="tv", no_title=None)
    assert db.media_result == 42
    assert not used
