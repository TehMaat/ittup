# -*- coding: utf-8 -*-
import base64
import re
from types import SimpleNamespace

import pytest

from ittup.common import config_settings
from ittup.common.external_services import imageHost
from ittup.common.external_services.igdb.client import IGDBClient
from ittup.common.external_services.igdb.core.models.search import Game
from ittup.common.external_services.igdb.description import GameImages, game_bbcode
from ittup.common.external_services.imageHost import ImgBB

from test_igdb_game import igdb_game

HOST_KEYS = ["IMGBB_KEY", "FREE_IMAGE_KEY", "LENSDUMP_KEY", "PTSCREENS_KEY", "IMGFI_KEY", "PASSIMA_KEY", "IMARIDE_KEY"]


class FakeIGDBImages:
    """ images.igdb.com without network: every image is downloaded, except those in `missing` """

    def __init__(self, missing=()):
        self.missing = set(missing)
        self.downloaded = []

    def get_url(self, url):
        self.downloaded.append(url)
        if any(image_id in url for image_id in self.missing):
            return None
        return SimpleNamespace(status_code=200, content=url.encode())


@pytest.fixture
def hosts(monkeypatch):
    """ Only ImgBB has a key, with the quorum on: an image it refuses fails """
    for key in HOST_KEYS:
        monkeypatch.setattr(config_settings.tracker_config, key, "no_key")
    monkeypatch.setattr(config_settings.tracker_config, "IMGBB_KEY", "imgbb-key")
    monkeypatch.setattr(config_settings.user_preferences, "SCREENSHOTS_QUORUM", True)
    monkeypatch.setattr(ImgBB, "priority", 0)
    state = {"refused": set(), "uploads": []}

    def upload(self):
        # The uploader holds the image base64 encoded: the fake download returns the URL as content
        source = base64.b64decode(self.image).decode()
        if any(image_id in source for image_id in state["refused"]):
            return None
        state["uploads"].append(source)
        return {"data": {"image": {"url": f"https://ImgBB/{source.rsplit('/', 1)[-1]}"}}}

    monkeypatch.setattr(imageHost.ImageUploader, "upload", upload)
    return state


def full_description(hosts) -> str:
    cover, screenshots = GameImages(http=FakeIGDBImages(), filename="Cyberpunk").upload_all(
        Game.from_igdb(igdb_game()))
    return game_bbcode(Game.from_igdb(igdb_game()), cover=cover, screenshots=screenshots)


def test_the_sections_in_order(hosts):
    description = full_description(hosts)

    order = ["[img=264]https://ImgBB/co7497.jpg", "[b]Cyberpunk 2077 (2020)[/b]", "[table]",
             "[b]Descrizione[/b]\nAn open world action RPG", "[b]Screenshot[/b]", "[spoiler=Trailer]",
             "[url=https://www.igdb.com/games/cyberpunk-2077]IGDB[/url]"]
    positions = [description.index(part) for part in order]
    assert positions == sorted(positions)
    assert description.count("[img=400]") == 2
    assert "images.igdb.com" not in description
    assert "t_cover_big/co7497" in hosts["uploads"][0]


def test_the_information_table(hosts):
    description = full_description(hosts)

    for row in ["[b]Piattaforme[/b][/td][td]PC (Microsoft Windows), PlayStation 5",
                "[b]Genere[/b][/td][td]Role-playing (RPG), Shooter", "[b]Sviluppatore[/b][/td][td]CD Projekt RED",
                "[b]Publisher[/b][/td][td]CD Projekt[/td]", "[b]Data di uscita[/b][/td][td]10/12/2020",
                "[b]Modalità[/b][/td][td]Single player"]:
        assert row in description


def test_only_unit3d_tags(hosts):
    tags = set(re.findall(r"\[/?([a-z*]+)", full_description(hosts)))
    assert tags <= {"center", "img", "url", "table", "tr", "td", "b", "spoiler", "youtube"}


def test_missing_fields_leave_out_their_sections():
    description = game_bbcode(Game.from_igdb({"id": 5, "name": "Obscure", "genres": [{"id": 1, "name": "Puzzle"}]}))

    assert description.startswith("[center][b]Obscure[/b][/center]")
    assert "[b]Genere[/b][/td][td]Puzzle" in description
    for missing in ["Piattaforme", "Sviluppatore", "Publisher", "Data di uscita", "Modalità", "[img", "Descrizione",
                    "Screenshot", "[youtube]", "IGDB[/url]"]:
        assert missing not in description


def test_no_cover_and_no_screenshot_no_images(hosts):
    game = Game.from_igdb(igdb_game(cover=None, screenshots=[]))
    http = FakeIGDBImages()

    assert GameImages(http=http, filename="Game").upload_all(game) == (None, [])
    assert http.downloaded == []


def test_at_most_four_screenshots(hosts):
    screenshots = [{"image_id": f"sc{number}"} for number in range(1, 8)]
    game = Game.from_igdb(igdb_game(screenshots=screenshots))

    _, urls = GameImages(http=FakeIGDBImages(), filename="Game").upload_all(game)

    assert urls == [f"https://ImgBB/sc{number}.jpg" for number in range(1, 5)]
    assert game_bbcode(game, screenshots=[f"https://ImgBB/{n}" for n in range(7)]).count("[img=400]") == 4


def test_no_image_host_with_a_key(monkeypatch, hosts):
    monkeypatch.setattr(config_settings.tracker_config, "IMGBB_KEY", "no_key")
    http = FakeIGDBImages()

    assert GameImages(http=http, filename="Game").upload_all(Game.from_igdb(igdb_game())) == (None, [])
    # No host: nothing downloaded
    assert http.downloaded == []


def test_a_failed_image_is_skipped_with_the_quorum_on(hosts):
    # sc1 is not downloaded, the image host refuses the cover: only sc2 is left, and nothing raises
    hosts["refused"].add("co7497")
    cover, screenshots = GameImages(http=FakeIGDBImages(missing=["sc1"]), filename="Game").upload_all(
        Game.from_igdb(igdb_game()))

    assert cover is None
    assert screenshots == ["https://ImgBB/sc2.jpg"]
    description = game_bbcode(Game.from_igdb(igdb_game()), cover=cover, screenshots=screenshots)
    assert "[img=264]" not in description
    assert description.count("[img=400]") == 1


def test_not_logged_in_no_images(hosts):
    assert GameImages(http=None, filename="Game").upload_all(Game.from_igdb(igdb_game())) == (None, [])


def test_the_chosen_game_gets_the_description(monkeypatch, hosts):
    client = IGDBClient()
    client.igdb.http_client = FakeIGDBImages()
    monkeypatch.setattr(client.igdb, "request", lambda query, endpoint: [igdb_game()])
    monkeypatch.setattr(client.viewer, "view_results", lambda igdb_results: None)

    game = client.game(content=SimpleNamespace(igdb_id=1877, display_name="Cyberpunk 2077"))

    assert game.description.startswith("[center][img=264]https://ImgBB/co7497.jpg[/img][/center]")
