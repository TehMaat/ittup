# -*- coding: utf-8 -*-
from types import SimpleNamespace

from ittup.common.external_services.igdb.client import GAME_FIELDS, IGDBClient
from ittup.common.external_services.igdb.core.models.search import ExternalGame, Game, Video


def igdb_game(**fields) -> dict:
    """ An IGDB 'games' result with the expanded fields """
    data = {
        "id": 1877,
        "name": "Cyberpunk 2077",
        "summary": "An open world action RPG",
        "url": "https://www.igdb.com/games/cyberpunk-2077",
        "first_release_date": 1607558400,
        "cover": {"id": 1, "image_id": "co7497"},
        "screenshots": [{"id": 2, "image_id": "sc1"}, {"id": 3, "image_id": "sc2"}],
        "platforms": [{"id": 6, "name": "PC (Microsoft Windows)"}, {"id": 167, "name": "PlayStation 5"}],
        "genres": [{"id": 12, "name": "Role-playing (RPG)"}, {"id": 5, "name": "Shooter"}],
        "game_modes": [{"id": 1, "name": "Single player"}],
        "involved_companies": [
            {"id": 10, "company": {"id": 908, "name": "CD Projekt RED"}, "developer": True, "publisher": False},
            {"id": 11, "company": {"id": 909, "name": "CD Projekt"}, "developer": False, "publisher": True},
        ],
        "videos": [{"id": 20, "name": "Gameplay", "video_id": "gameplay1"},
                   {"id": 21, "name": "Official Launch TRAILER", "video_id": "trailer1"}],
        "external_games": [{"id": 30, "uid": "1091500", "external_game_source": 1},
                           {"id": 31, "uid": "1423049311", "external_game_source": 5}],
    }
    data.update(fields)
    return data


def test_every_field_of_the_expanded_result():
    game = Game.from_igdb(igdb_game())

    assert (game.id, game.name, game.summary) == (1877, "Cyberpunk 2077", "An open world action RPG")
    assert game.first_release_date == 1607558400
    assert game.cover == "co7497"
    assert game.screenshots == ["sc1", "sc2"]
    assert game.platforms == ["PC (Microsoft Windows)", "PlayStation 5"]
    assert game.genres == ["Role-playing (RPG)", "Shooter"]
    assert game.game_modes == ["Single player"]
    assert game.developers == ["CD Projekt RED"]
    assert game.publishers == ["CD Projekt"]
    assert game.videos[1] == Video(name="Official Launch TRAILER", video_id="trailer1")
    assert game.external_games == [ExternalGame(uid="1091500", source=1), ExternalGame(uid="1423049311", source=5)]


def test_missing_fields_are_empty():
    game = Game.from_igdb({"id": 5, "name": "Obscure"})

    assert game.summary == ""
    assert game.first_release_date is None
    assert game.cover == ""
    assert game.screenshots == game.platforms == game.genres == game.game_modes == []
    assert game.developers == game.publishers == game.videos == game.external_games == []
    assert game.trailer is None


def test_the_trailer_is_the_first_video_with_trailer_in_the_name():
    assert Game.from_igdb(igdb_game()).trailer.video_id == "trailer1"


def test_without_trailer_in_the_name_the_first_video():
    videos = [{"name": "Gameplay", "video_id": "gameplay1"}, {"name": "Teaser", "video_id": "teaser1"}]
    assert Game.from_igdb(igdb_game(videos=videos)).trailer.video_id == "gameplay1"


def test_a_single_trailer_in_the_description():
    description = IGDBClient.game_description(Game.from_igdb(igdb_game())).description

    assert description.count("[youtube]") == 1
    assert "[youtube]trailer1[/youtube]" in description


def test_no_video_no_trailer_section():
    description = IGDBClient.game_description(Game.from_igdb(igdb_game(videos=[]))).description

    assert "[youtube]" not in description
    assert "No trailers" not in description


def requests(monkeypatch, client: IGDBClient) -> list:
    sent = []

    def request(query, endpoint):
        sent.append((endpoint, query))
        return [igdb_game()]

    monkeypatch.setattr(client.igdb, "request", request)
    return sent


def test_the_search_filters_on_game_type(monkeypatch):
    client = IGDBClient()
    sent = requests(monkeypatch, client)

    client.search(title="Cyberpunk", platform_name="6")

    query = sent[0][1]
    assert "game_type = (0, 1, 2, 8, 9, 10)" in query
    assert "category" not in query


def test_every_field_in_a_single_query(monkeypatch):
    client = IGDBClient()
    sent = requests(monkeypatch, client)
    monkeypatch.setattr(client.viewer, "view_results", lambda igdb_results: None)

    game = client.game(content=SimpleNamespace(igdb_id=1877))

    # No request to game_videos for each video: one query to games
    assert [endpoint for endpoint, _ in sent] == ["games"]
    assert sent[0][1].startswith(GAME_FIELDS)
    for field in ["cover.image_id", "screenshots.image_id", "involved_companies.company.name", "videos.video_id",
                  "external_games.uid", "external_games.external_game_source"]:
        assert field in GAME_FIELDS
    assert game.trailer.video_id == "trailer1"


def test_search_title_and_id_use_the_same_fields(monkeypatch):
    client = IGDBClient()
    sent = requests(monkeypatch, client)

    client.search_no_platform(title="Cyberpunk")
    client.search_by_id(igdb_id=1877)

    assert all(query.startswith(GAME_FIELDS) for _, query in sent)
