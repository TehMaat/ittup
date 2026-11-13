# -*- coding: utf-8 -*-
import json
import re
from types import SimpleNamespace

import httpx
import pytest

from ittup.common import config_settings
from ittup.common.external_services.igdb.client import IGDBClient
from ittup.common.external_services.igdb.core.models.search import Game
from ittup.common.external_services.igdb.description import game_bbcode
from ittup.common.external_services.steam.bbcode import html_to_bbcode, requirements_to_bbcode
from ittup.common.external_services.steam.client import SteamApp, SteamClient
from ittup.common.lookup_cache import LookupCache

from test_igdb_game import igdb_game

MINIMUM = ('<strong>Minimi:</strong><br><ul class="bb_ul"><li>Richiede un processore e un sistema operativo a 64 bit<br>'
           '</li><li><strong>Sistema operativo:</strong> Windows 10 64-bit<br></li><li><strong>Memoria:</strong>'
           ' 12 GB di RAM<br></li><li><strong>Note aggiuntive:</strong> SSD &amp; 70 GB</li></ul>')
RECOMMENDED = ('<strong>Consigliati:</strong><br><ul class="bb_ul"><li><strong>Sistema operativo:</strong>'
               ' Windows 10 64-bit<br></li><li><strong>Memoria:</strong> 16 GB di RAM</li></ul>')
SHORT_DESCRIPTION = "Cyberpunk 2077 &egrave; un GDR d&#39;azione a mondo aperto ambientato a Night City."


def appdetails(appid="1091500", success=True, **data) -> dict:
    payload = {"short_description": SHORT_DESCRIPTION,
               "pc_requirements": {"minimum": MINIMUM, "recommended": RECOMMENDED}}
    payload.update(data)
    return {appid: {"success": success, "data": payload} if success else {"success": False}}


class FakeSteam:
    """ store.steampowered.com without network """

    def __init__(self, answer=None, error=None):
        self.answer = answer
        self.error = error
        self.requests = []

    def get_url(self, url, params=None):
        self.requests.append((url, params))
        if self.error:
            raise self.error
        if self.answer is None:
            return None
        content = self.answer if isinstance(self.answer, str) else json.dumps(self.answer)
        return httpx.Response(200, content=content.encode())


def pc() -> SimpleNamespace:
    return SimpleNamespace(platform_list=["PC"], display_name="Cyberpunk 2077")


def steam_app(answer, content=None, game=None) -> tuple[SteamApp | None, FakeSteam]:
    http = FakeSteam(answer)
    app = SteamClient(http=http).app(game=game or Game.from_igdb(igdb_game()), content=content or pc())
    return app, http


def test_html_to_bbcode():
    assert html_to_bbcode(MINIMUM) == (
        "[b]Minimi:[/b]\n[list]\n[*]Richiede un processore e un sistema operativo a 64 bit\n"
        "[*][b]Sistema operativo:[/b] Windows 10 64-bit\n[*][b]Memoria:[/b] 12 GB di RAM\n"
        "[*][b]Note aggiuntive:[/b] SSD & 70 GB\n[/list]")


def test_other_tags_removed_and_entities_decoded():
    assert html_to_bbcode('<p>Un <a href="https://example.org">gioco</a> &quot;bello&quot;<br/>'
                          '<span class="x">&lt;3</span></p>') == 'Un gioco "bello"\n<3'


def test_requirements_without_the_steam_label():
    assert requirements_to_bbcode(RECOMMENDED).startswith("[list]\n[*][b]Sistema operativo:[/b]")


def test_complete_requirements():
    app, http = steam_app(appdetails())

    assert http.requests == [("https://store.steampowered.com/api/appdetails", {"appids": "1091500", "l": "italian"})]
    description = game_bbcode(Game.from_igdb(igdb_game()), steam=app)

    order = ["[b]Descrizione[/b]\nCyberpunk 2077 è un GDR d'azione", "[b]Requisiti di sistema[/b]",
             "[b]Minimi[/b]\n[list]\n[*]Richiede", "[b]Consigliati[/b]\n[list]\n[*][b]Sistema operativo:[/b]",
             "[url=https://www.igdb.com/games/cyberpunk-2077]IGDB[/url] · "
             "[url=https://store.steampowered.com/app/1091500/]Steam[/url]"]
    positions = [description.index(part) for part in order]
    assert positions == sorted(positions)
    assert "An open world action RPG" not in description
    assert "Minimi:" not in description
    assert set(re.findall(r"\[/?([a-z*]+)", description)) <= {"center", "b", "table", "tr", "td", "list", "*",
                                                              "spoiler", "youtube", "url"}


def test_only_minimum_requirements():
    app, _ = steam_app(appdetails(pc_requirements={"minimum": MINIMUM}))
    description = game_bbcode(Game.from_igdb(igdb_game()), steam=app)

    assert "[b]Minimi[/b]" in description
    assert "Consigliati" not in description


def test_no_requirements_on_steam():
    # Steam returns an empty list for a game without requirements
    app, _ = steam_app(appdetails(pc_requirements=[]))
    description = game_bbcode(Game.from_igdb(igdb_game()), steam=app)

    assert "Requisiti di sistema" not in description
    assert "store.steampowered.com/app/1091500" in description


def test_empty_short_description_keeps_the_igdb_summary():
    app, _ = steam_app(appdetails(short_description=""))
    assert "[b]Descrizione[/b]\nAn open world action RPG" in game_bbcode(Game.from_igdb(igdb_game()), steam=app)


@pytest.mark.parametrize("answer, error", [
    (appdetails(success=False), None),
    ("<html>not JSON</html>", None),
    ({"1091500": {"success": True, "data": []}}, None),
    (None, None),
    (None, httpx.ReadTimeout("timeout")),
])
def test_no_answer_from_steam_no_requirements(answer, error):
    http = FakeSteam(answer, error)
    app = SteamClient(http=http).app(game=Game.from_igdb(igdb_game()), content=pc())

    assert app is None
    description = game_bbcode(Game.from_igdb(igdb_game()), steam=app)
    assert "Requisiti di sistema" not in description
    assert "steampowered" not in description
    assert "[b]Descrizione[/b]\nAn open world action RPG" in description


def test_not_a_pc_game_no_request():
    app, http = steam_app(appdetails(), content=SimpleNamespace(platform_list=["PS5"]))
    assert app is None
    assert http.requests == []


def test_no_steam_external_game_no_request():
    # Only GOG (5) on IGDB
    game = Game.from_igdb(igdb_game(external_games=[{"uid": "1423049311", "external_game_source": 5}]))
    app, http = steam_app(appdetails(), game=game)
    assert app is None
    assert http.requests == []


def test_one_request_for_each_game_in_the_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(config_settings.user_preferences, "CACHE_DBONLINE", True)
    monkeypatch.setattr(config_settings.user_preferences, "CACHE_PATH", str(tmp_path))
    monkeypatch.setattr(LookupCache, "_cache", None)
    try:
        http = FakeSteam(appdetails())
        first = SteamClient(http=http).app(game=Game.from_igdb(igdb_game()), content=pc())
        second = SteamClient(http=http).app(game=Game.from_igdb(igdb_game()), content=pc())
    finally:
        if LookupCache._cache is not None:
            LookupCache._cache.close()
        LookupCache._cache = None

    assert first == second
    assert len(http.requests) == 1


def test_the_pc_game_description_has_the_steam_data(monkeypatch):
    for key in ["IMGBB_KEY", "FREE_IMAGE_KEY", "LENSDUMP_KEY", "PTSCREENS_KEY", "IMGFI_KEY", "PASSIMA_KEY",
                "IMARIDE_KEY"]:
        monkeypatch.setattr(config_settings.tracker_config, key, "no_key")
    client = IGDBClient()
    client.igdb.http_client = FakeSteam(appdetails())
    monkeypatch.setattr(client.igdb, "request", lambda query, endpoint: [igdb_game()])
    monkeypatch.setattr(client.viewer, "view_results", lambda igdb_results: None)

    game = client.game(content=SimpleNamespace(igdb_id=1877, display_name="Cyberpunk 2077", platform_list=["pc"]))

    assert "[b]Requisiti di sistema[/b]" in game.description
    assert "[url=https://store.steampowered.com/app/1091500/]Steam[/url]" in game.description
