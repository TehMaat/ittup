# -*- coding: utf-8 -*-
import pytest

from ittup.common.utility import ManageTitles


@pytest.mark.parametrize("name, pack", [
    ("Show S04 1080p WEB-DL", "S04"),
    ("Show S04E01-06 1080p WEB-DL", "S04E01-06"),
    ("Show S04E01-E06 1080p WEB-DL", "S04E01-E06"),
    # A space or a dot between the season and the episodes
    ("Show S04 E01-06 1080p WEB-DL", "S04E01-06"),
    ("Show.S04.E01-06.1080p.WEB-DL", "S04E01-06"),
    ("Show S4 E1 - 6 1080p", "S04E01-06"),
    # Single episodes
    ("Show S04E01 1080p WEB-DL", None),
    ("Show S04 E01 1080p WEB-DL", None),
    ("Show S04E01-1080p", None),
    ("Show.S01E01.1080p.DTS5.1.mkv", None),
    ("/tv/Show S01/Show.S01E01.1080p.mkv", None),
    # Lower case
    ("show.s04.1080p.web-dl", "S04"),
    ("show.s04e01-e06.1080p", "S04E01-E06"),
])
def test_season_pack(name, pack):
    assert ManageTitles.season_pack(name) == pack


def test_pack_episodes():
    assert ManageTitles.pack_episodes("S04E01-06") == (4, 1, 6)
    assert ManageTitles.pack_episodes("S04E01-E10") == (4, 1, 10)
    assert ManageTitles.pack_episodes("S04") is None
    assert ManageTitles.pack_episodes(None) is None


def details(episode_count: int, next_season: int | None = None) -> dict:
    return {"seasons": [{"season_number": 3, "episode_count": 8}, {"season_number": 4, "episode_count": episode_count}],
            "next_episode_to_air": {"season_number": next_season} if next_season else None}


def test_full_season_pack_is_the_season():
    from ittup.core.media_manager.VideoManager import VideoManager
    assert VideoManager.full_season("S04E01-10", details(10)) == "S04"
    assert VideoManager.full_season("S04E01-E10", details(10)) == "S04"


def test_partial_or_ongoing_season_keeps_the_episodes():
    from ittup.core.media_manager.VideoManager import VideoManager
    assert VideoManager.full_season("S04E01-06", details(10)) is None
    assert VideoManager.full_season("S04E02-10", details(10)) is None
    assert VideoManager.full_season("S04E01-10", details(10, next_season=4)) is None
    assert VideoManager.full_season("S04E01-10", None) is None
    assert VideoManager.full_season("S04", details(10)) is None
