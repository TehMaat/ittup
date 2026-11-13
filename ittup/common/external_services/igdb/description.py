# -*- coding: utf-8 -*-
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from ittup.common.external_services.igdb.core.models.search import Game
from ittup.common.external_services.imageHost import UPLOAD_WORKERS, Build
from ittup.common.external_services.sessions.session import MyHttp
from ittup.view import custom_console

IGDB_IMAGE_URL = "https://images.igdb.com/igdb/image/upload/{size}/{image_id}.jpg"

# Screenshots of the game in the description
MAX_SCREENSHOTS = 4

# Width of the images on the torrent page: the cover is 264×374 (t_cover_big), a screenshot 889×500
COVER_WIDTH = 264
SCREENSHOT_WIDTH = 400


class GameImages:
    """
    Cover and screenshots of a game, downloaded from IGDB and uploaded again on the image hosts with a key in
    settings.json: the description has no link to images.igdb.com
    """

    def __init__(self, http: MyHttp | None, filename: str):
        self.http = http
        self.build = Build(extracted_frames=[], filename=filename)

    def download(self, image_id: str, size: str) -> bytes | None:
        if self.http is None:
            return None
        url = IGDB_IMAGE_URL.format(size=size, image_id=image_id)
        try:
            response = self.http.get_url(url)
        except Exception as e:
            custom_console.bot_warning_log(f"IGDB image '{url}' not downloaded: {e!r}")
            return None
        if response is None or response.status_code != 200 or not response.content:
            custom_console.bot_warning_log(f"IGDB image '{url}' not downloaded")
            return None
        return response.content

    def upload(self, number: int, image_id: str, size: str) -> str | None:
        image = self.download(image_id=image_id, size=size)
        if image is None:
            return None
        uploaded = self.build.safe_upload_image(number, image)
        return uploaded.url if uploaded else None

    def upload_all(self, game: Game) -> tuple[str | None, list[str]]:
        """
        The URL of the cover and of the screenshots on the image hosts. The images are decorative: an image that
        fails is skipped, without stopping the upload of the game (SCREENSHOTS_QUORUM doesn't apply)
        """
        images = ([(game.cover, "t_cover_big")] if game.cover else []) + [
            (image_id, "t_screenshot_big") for image_id in game.screenshots[:MAX_SCREENSHOTS]]
        if not images:
            return None, []

        if not self.build.has_any_key():
            custom_console.bot_warning_log("No image host API key found in settings.json:"
                                           " the game description has no images")
            return None, []

        with ThreadPoolExecutor(max_workers=UPLOAD_WORKERS) as executor:
            urls = list(executor.map(lambda item: self.upload(item[0], *item[1]), enumerate(images, start=1)))

        cover = urls.pop(0) if game.cover else None
        screenshots = [url for url in urls if url]
        failed = len(images) - len(screenshots) - (1 if cover else 0)
        if failed:
            custom_console.bot_warning_log(f"{failed} of {len(images)} game images not uploaded:"
                                           f" the description doesn't have them")
        return cover, screenshots


def release_date(game: Game) -> datetime | None:
    if game.first_release_date is None:
        return None
    try:
        return datetime.fromtimestamp(game.first_release_date, tz=timezone.utc)
    except (OverflowError, OSError, ValueError, TypeError):
        return None


def info_table(game: Game) -> str:
    """ Platforms, genre, developer, publisher, release date and modes: a row without data is left out """
    date = release_date(game)
    rows = [
        ("Piattaforme", ", ".join(game.platforms)),
        ("Genere", ", ".join(game.genres)),
        ("Sviluppatore", ", ".join(game.developers)),
        ("Publisher", ", ".join(game.publishers)),
        ("Data di uscita", date.strftime("%d/%m/%Y") if date else ""),
        ("Modalità", ", ".join(game.game_modes)),
    ]
    rows = [(label, value) for label, value in rows if value]
    if not rows:
        return ""
    return "[table]" + "".join(f"[tr][td][b]{label}[/b][/td][td]{value}[/td][/tr]" for label, value in rows) + "[/table]"


def game_bbcode(game: Game, cover: str | None = None, screenshots: list[str] | None = None) -> str:
    """
    The description of a game, in sections: cover, title and year, information, description, screenshots,
    trailer and link to IGDB. A section without data is left out
    """
    sections = []
    if cover:
        sections.append(f"[center][img={COVER_WIDTH}]{cover}[/img][/center]")

    date = release_date(game)
    sections.append(f"[center][b]{game.name}{f' ({date.year})' if date else ''}[/b][/center]")

    table = info_table(game)
    if table:
        sections.append(table)

    if game.summary:
        sections.append(f"[b]Descrizione[/b]\n{game.summary}")

    if screenshots:
        sections.append("[b]Screenshot[/b]\n[center]" + "".join(
            f"[url={url}][img={SCREENSHOT_WIDTH}]{url}[/img][/url]" for url in screenshots[:MAX_SCREENSHOTS])
                        + "[/center]")

    trailer = game.trailer
    if trailer:
        sections.append(f"[spoiler=Trailer][center][youtube]{trailer.video_id}[/youtube][/center][/spoiler]")

    if game.url.startswith("http"):
        sections.append(f"[url={game.url}]IGDB[/url]")

    return "\n\n".join(sections) + "\n"
