# -*- coding: utf-8 -*-
from types import SimpleNamespace

from ittup.common.external_services.igdb.client import IGDBClient


def fake_results() -> list[dict]:
    return [
        {"id": 101, "name": "Game One", "summary": "First summary", "videos": [1], "url": "https://example.org/1"},
        {"id": 202, "name": "Game Two", "summary": "Second summary", "videos": [2], "url": "https://example.org/2"},
    ]


def make_client(monkeypatch, choice: int) -> IGDBClient:
    client = IGDBClient()
    # No network: no HTTP request
    monkeypatch.setattr(client.igdb, "request", lambda *args, **kwargs: None)
    # No console: the user picks the result at index `choice`
    monkeypatch.setattr(client.viewer, "view_results", lambda igdb_results: None)
    monkeypatch.setattr(client.viewer, "select_result", lambda results: choice)
    return client


def content() -> SimpleNamespace:
    return SimpleNamespace(display_name="game two", folder="Game.Two")


def test_user_enter_igdb_uses_the_chosen_result(monkeypatch):
    client = make_client(monkeypatch, choice=1)

    game = client.user_enter_igdb(igdb_results=fake_results(), content=content(), candidate="Game Two")

    assert game.id == 202
    assert game.name == "Game Two"


def test_user_enter_igdb_first_result(monkeypatch):
    client = make_client(monkeypatch, choice=0)

    game = client.user_enter_igdb(igdb_results=fake_results(), content=content(), candidate="Game One")

    assert game.id == 101
    assert game.name == "Game One"


def test_user_enter_igdb_skip(monkeypatch):
    client = make_client(monkeypatch, choice=None)

    assert client.user_enter_igdb(igdb_results=fake_results(), content=content(), candidate="Game One") is None
