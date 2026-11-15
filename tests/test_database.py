# -*- coding: utf-8 -*-
import sqlite3

import pytest

from ittup.common import database
from ittup.common.database import Database


@pytest.fixture
def cache_path(monkeypatch, tmp_path):
    monkeypatch.setattr(database.config_settings.user_preferences, "CACHE_PATH", str(tmp_path))
    return tmp_path


def _locked(path):
    """
    Another process writing the file: a connection holding the write lock
    """
    other = sqlite3.connect(path, isolation_level=None)
    other.execute("CREATE TABLE IF NOT EXISTS torrents (id INTEGER PRIMARY KEY, name TEXT)")
    other.execute("BEGIN EXCLUSIVE")
    return other


def test_a_database_that_is_never_written_does_not_touch_the_file(cache_path):
    Database(db_file="ITT")

    assert not (cache_path / "ITT.db").exists()


def test_a_database_locked_by_another_process_does_not_stop_the_duplicate_check(cache_path):
    # #156: the duplicate check created the Database, which dropped the table at once:
    # 'database is locked' when another process held the file
    other = _locked(str(cache_path / "ITT.db"))
    try:
        Database(db_file="ITT")
    finally:
        other.rollback()
        other.close()


def test_the_first_write_creates_the_table_again(cache_path):
    old = sqlite3.connect(cache_path / "ITT.db")
    old.execute("CREATE TABLE torrents (id INTEGER PRIMARY KEY, name TEXT)")
    old.execute("INSERT INTO torrents (name) VALUES ('old')")
    old.commit()
    old.close()

    db = Database(db_file="ITT")
    db.write({"name": "new", "genres": ["Drama"], "meta": {"poster": "p"}})
    db.write({"name": "other"})
    db.close()

    with sqlite3.connect(cache_path / "ITT.db") as check:
        rows = check.execute("SELECT name, genres, meta FROM torrents ORDER BY id").fetchall()
    assert rows == [("new", '["Drama"]', '{"poster": "p"}'), ("other", None, None)]


def test_close_before_a_write_does_nothing(cache_path):
    db = Database(db_file="ITT")
    db.close()

    assert not (cache_path / "ITT.db").exists()
