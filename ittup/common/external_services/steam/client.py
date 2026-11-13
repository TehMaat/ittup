# -*- coding: utf-8 -*-
from dataclasses import dataclass

from ittup.common.external_services.igdb.core.models.search import Game
from ittup.common.external_services.sessions.session import MyHttp
from ittup.common.external_services.steam.bbcode import html_to_bbcode, requirements_to_bbcode
from ittup.common.lookup_cache import LookupCache
from ittup.view import custom_console

# IGDB external_game_sources: the ID of Steam (the same value of the deprecated external_games.category)
STEAM_SOURCE = 1

# Not documented, no key: about 200 requests every 5 minutes, so one request for each game, in the cache
APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"
STORE_URL = "https://store.steampowered.com/app/{appid}/"
LANGUAGE = "italian"


@dataclass
class SteamApp:
    appid: str
    # BBCode, empty if Steam doesn't have them
    short_description: str
    minimum: str
    recommended: str

    @property
    def url(self) -> str:
        return STORE_URL.format(appid=self.appid)


def steam_appid(game: Game) -> str | None:
    """ The Steam appid of the game, None if IGDB doesn't link it to Steam """
    for external_game in game.external_games:
        if external_game.source == STEAM_SOURCE and external_game.uid:
            return external_game.uid
    return None


def is_pc(content: object) -> bool:
    return any(str(platform).upper() == "PC" for platform in getattr(content, "platform_list", None) or [])


class SteamClient:

    def __init__(self, http: MyHttp | None):
        self.http = http

    def appdetails(self, appid: str) -> dict | None:
        """
        The 'data' of the game on the Steam store, in Italian. None if Steam doesn't answer, answers
        'success: false' or with an invalid JSON: the game is uploaded anyway, without the Steam data
        """
        cached = LookupCache.get("steam", "appdetails", appid, LANGUAGE)
        if cached is not None:
            return cached
        if self.http is None:
            return None

        try:
            response = self.http.get_url(APPDETAILS_URL, params={"appids": appid, "l": LANGUAGE})
            payload = response.json() if response is not None and response.status_code == 200 else None
        except Exception as e:
            custom_console.bot_warning_log(f"Steam appdetails for app {appid}: {e!r}")
            return None

        entry = payload.get(str(appid)) if isinstance(payload, dict) else None
        if not isinstance(entry, dict) or not entry.get("success") or not isinstance(entry.get("data"), dict):
            custom_console.bot_warning_log(f"Steam has no data for app {appid}: no system requirements")
            return None
        LookupCache.set("steam", "appdetails", appid, LANGUAGE, value=entry["data"])
        return entry["data"]

    def app(self, game: Game, content: object) -> SteamApp | None:
        """
        The Steam data of a PC game that IGDB links to Steam, None for the other games
        """
        if not is_pc(content):
            return None
        appid = steam_appid(game)
        if not appid:
            return None
        data = self.appdetails(appid)
        if not data:
            return None
        # Steam returns an empty list, not an object, for a game without requirements
        requirements = data.get("pc_requirements")
        requirements = requirements if isinstance(requirements, dict) else {}
        return SteamApp(
            appid=appid,
            short_description=html_to_bbcode(str(data.get("short_description") or "")),
            minimum=requirements_to_bbcode(str(requirements.get("minimum") or "")),
            recommended=requirements_to_bbcode(str(requirements.get("recommended") or "")),
        )
