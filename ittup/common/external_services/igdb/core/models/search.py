# -*- coding: utf-8 -*-

from dataclasses import dataclass, field


@dataclass
class Video:
    name: str
    video_id: str


@dataclass
class ExternalGame:
    # The ID of the game on the other service (e.g. the Steam appid)
    uid: str
    # The service (IGDB external_game_sources, e.g. 1 = Steam)
    source: int | None


@dataclass
class Game:
    id: int
    name: str
    summary: str
    url: str
    # Unix time, None if IGDB doesn't know it
    first_release_date: int | None = None
    # IGDB image_id of the cover and of the screenshots
    cover: str = ""
    screenshots: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    genres: list[str] = field(default_factory=list)
    game_modes: list[str] = field(default_factory=list)
    developers: list[str] = field(default_factory=list)
    publishers: list[str] = field(default_factory=list)
    videos: list[Video] = field(default_factory=list)
    external_games: list[ExternalGame] = field(default_factory=list)
    description: str = field(default="", init=False)

    @property
    def trailer(self) -> Video | None:
        """
        The first video with 'trailer' in its name, otherwise the first video
        """
        for video in self.videos:
            if "trailer" in video.name.lower():
                return video
        return self.videos[0] if self.videos else None

    @staticmethod
    def names(items: list | None) -> list[str]:
        """ The 'name' of each expanded IGDB item ({'id': 6, 'name': 'PC (Microsoft Windows)'}) """
        return [item["name"] for item in items or [] if isinstance(item, dict) and item.get("name")]

    @classmethod
    def from_igdb(cls, data: dict) -> "Game":
        """
        A game from an IGDB 'games' result with the expanded fields: a field IGDB doesn't return stays empty
        """
        cover = data.get("cover")
        companies = [company for company in data.get("involved_companies") or [] if isinstance(company, dict)]
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            summary=data.get("summary", ""),
            url=data.get("url", "there is no page url for this game"),
            first_release_date=data.get("first_release_date"),
            cover=cover.get("image_id", "") if isinstance(cover, dict) else "",
            screenshots=[screenshot["image_id"] for screenshot in data.get("screenshots") or []
                         if isinstance(screenshot, dict) and screenshot.get("image_id")],
            platforms=cls.names(data.get("platforms")),
            genres=cls.names(data.get("genres")),
            game_modes=cls.names(data.get("game_modes")),
            developers=cls.names([company.get("company") for company in companies if company.get("developer")]),
            publishers=cls.names([company.get("company") for company in companies if company.get("publisher")]),
            videos=[Video(name=video.get("name") or "", video_id=video["video_id"])
                    for video in data.get("videos") or [] if isinstance(video, dict) and video.get("video_id")],
            external_games=[ExternalGame(uid=str(game["uid"]), source=game.get("external_game_source"))
                            for game in data.get("external_games") or []
                            if isinstance(game, dict) and game.get("uid")],
        )
