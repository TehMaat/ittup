# -*- coding: utf-8 -*-
import json
import os
import re

from ittup.common.external_services.igdb.core.tags import crew_patterns, platform_patterns
from ittup.common.title import Guessit
from ittup.common.utility import ManageTitles, System
from ittup.common.mediainfo import MediaFile
from ittup.common import title
from ittup.view import custom_console

# Resolution, minimum width, minimum height. A video that is not 16:9 is reduced on one side only: the height for
# the scope movies (1920x800), the width for the 4:3 and the anamorphic ones (1440x1080). The resolution is the
# highest one reached by either side
RESOLUTION_THRESHOLDS = (
    ("2160p", 3200, 1800),
    ("1080p", 1600, 900),
    ("720p", 1100, 600),
    ("576p", 960, 540),
)

# The interlaced resolutions of the tracker: 2160p and 720p are always progressive
INTERLACED_RESOLUTIONS = {"1080p": "1080i", "576p": "576i", "480p": "480i"}

# MediaInfo 'Scan type' of an interlaced video (MBAFF/PAFF: interlaced H.264). 'Mixed' is progressive
INTERLACED_SCAN_TYPES = {"interlaced", "mbaff", "paff"}


class Media:
    def __init__(self, folder: str, subfolder: str):
        self.folder: str = folder
        self.subfolder: str = subfolder
        self.title: str = os.path.basename(os.path.join(self.folder, self.subfolder))

        # // Media
        self._crew_list: list[str] | None = None
        self._game_title: str | None = None
        self._platform_list: list[str] | None = None
        self._title_sanitized: str | None = None
        self._guess_title: str | None = None
        self._guess_filename: Guessit | None = None
        self._guess_season: int | None = None
        self._episode: int | None = None
        self._source: str | None = None
        self._screen_size: str | None = None
        self._audio_codec: str | None = None
        self._subtitle: str | None = None
        self._torrent_path: str | None = None

        # // Contents
        self._file_name: str | None = None
        self._display_name: str | None = None
        self._category: int | None = None
        self._audio_languages: list[str] = []
        self._media_file: MediaFile | None = None
        self._languages: list[str] | None = None
        self._resolution: str | None = None
        self._tracker_name: str | None = None

        # // Contents dall'esterno
        self._torrent_name: str | None = None
        self._size: int = 0
        self._metainfo: str | None = None
        self._torrent_pack: bool = False
        self._pack: str | None = None
        self._doc_description: str | None = None
        self._game_nfo: str | None = None
        self._tmdb_id: int | None = None
        self._imdb_id: int | None = None
        self._tvdb_id: int | None = None
        self._igdb_id: int | None = None
        self._generate_title: str | None = None
        # Source read from MediaInfo when the name has none (es. 'BluRay REMUX'), for the tracker type
        self.mediainfo_source: str | None = None
        # What the file names should say according to the title and MediaInfo (RENAME_FILES)
        self.title_info = None

    def move_to(self, path: str) -> None:
        """
        The media was renamed: point it to its new path
        """
        self.folder = os.path.dirname(path)
        self.subfolder = path
        self.title = os.path.basename(path)
        self._title_sanitized = None
        self._guess_title = None
        self._guess_filename = None
        self._guess_season = None
        self._episode = None
        self._torrent_path = None
        self._crew_list = None
        self._platform_list = None
        self._category = None

    def renamed(self, path: str, renamed_files: dict[str, str]) -> None:
        """
        The files were renamed as the title after the analysis: point the media to the new paths
        and keep what was read from the old name (category, season, episode, MediaInfo)
        """
        category, season, episode = self.category, self.guess_season, self.guess_episode
        old_file_name = self.file_name
        is_folder = os.path.isdir(path)
        self.move_to(path)
        self._category, self._guess_season, self._episode = category, season, episode
        self.torrent_name = os.path.basename(path)

        if is_folder:
            file = os.path.basename(old_file_name)
            self.file_name = os.path.join(path, renamed_files.get(file, file))
            meta = [{**item, "path": [renamed_files.get(item["path"][0], item["path"][0])]}
                    for item in json.loads(self.metainfo)]
        else:
            self.file_name = path
            meta = [{**item, "path": [path]} for item in json.loads(self.metainfo)]
        self.metainfo = json.dumps(meta, indent=4)
        if self._media_file:
            self._media_file.file_path = self.file_name

    @property
    def title_sanitized(self) -> str:
        if not self._title_sanitized:
            self._title_sanitized = ManageTitles.clean_text(self.title)
        return self._title_sanitized

    @property
    def title_sanitize_tags(self) -> str:
        self._title_sanitized = ManageTitles.clean_tags(self.title)
        return self._title_sanitized

    @property
    def crew_list(self) -> list['str']:
        if not self._crew_list:
            self._crew_list = self._crew(filename=self.title_sanitized)
        return self._crew_list

    @property
    def platform_list(self) -> list['str']:
        if not self._platform_list:
            self._platform_list = self._platform(filename=self.title_sanitized)
        return self._platform_list

    @property
    def game_nfo(self) -> str:
        return self._game_nfo

    @game_nfo.setter
    def game_nfo(self, value):
        self._game_nfo = value

    @property
    def game_title(self):
        if not self._game_title:
            # Remove the crew name to help IGDB with searching
            _game_tmp = self.guess_filename.guessit_title
            for crew in self.crew_list:
                _game_tmp = _game_tmp.replace(crew, " ")
            self._game_title = _game_tmp.strip()
        return self._game_title

    @property
    def torrent_name(self) -> str:
        return self._torrent_name

    @torrent_name.setter
    def torrent_name(self, value):
        self._torrent_name = value

    @property
    def size(self) -> int:
        return self._size

    @size.setter
    def size(self, value):
        self._size = value

    @property
    def metainfo(self) -> str:
        return self._metainfo

    @metainfo.setter
    def metainfo(self, value):
        self._metainfo = value

    @property
    def doc_description(self) -> str:
        return self._doc_description

    @doc_description.setter
    def doc_description(self, value):
        self._doc_description = value

    @property
    def tracker_name(self) -> str:
        return self._tracker_name

    @tracker_name.setter
    def tracker_name(self, value):
        self._tracker_name = value

    @property
    def torrent_pack(self) -> bool:
        return self._torrent_pack

    @torrent_pack.setter
    def torrent_pack(self, value):
        self._torrent_pack = value

    @property
    def pack(self) -> str | None:
        return self._pack

    @pack.setter
    def pack(self, value):
        self._pack = value

    @property
    def tmdb_id(self) -> int:
        return self._tmdb_id

    @tmdb_id.setter
    def tmdb_id(self, value):
        self._tmdb_id = value

    @property
    def imdb_id(self) -> int:
        return self._imdb_id

    @imdb_id.setter
    def imdb_id(self, value):
        self._imdb_id = value

    @property
    def tvdb_id(self) -> int:
        return self._tvdb_id

    @tvdb_id.setter
    def tvdb_id(self, value):
        self._tvdb_id = value

    @property
    def igdb_id(self) -> int:
        return self._igdb_id

    @igdb_id.setter
    def igdb_id(self, value):
        self._igdb_id = value

    @property
    def guess_filename(self):
        if not self._guess_filename:
            self._guess_filename = title.Guessit(self.title_sanitized)
        return self._guess_filename

    @property
    def file_name(self):
        return self._file_name

    @file_name.setter
    def file_name(self, value):
        self._file_name = value

    @property
    def display_name(self):
        return self._display_name

    @display_name.setter
    def display_name(self, value):
        self._display_name = value

    @property
    def guess_title(self) -> str:
        if not self._guess_title:
            self._guess_title = title.Guessit(self.title_sanitized).guessit_title.strip()
        return self._guess_title

    @guess_title.setter
    def guess_title(self, value):
        self._guess_title = value

    @property
    def guess_season(self):
        if not self._guess_season:
            if 'tv' in self.category:
                self._guess_season = self.guess_filename.guessit_season
        return self._guess_season

    @property
    def guess_episode(self):
        if not self._episode:
            if 'tv' in self.category:
                self._episode = self.guess_filename.guessit_episode
        return self._episode

    @property
    def source(self):
        if not self._source:
            self._source = self.guess_filename.source
        return self._source

    @property
    def audio_codec(self):
        if not self._audio_codec:
            self._audio_codec = self.guess_filename.audio_codec
        return self._audio_codec

    @property
    def audio_languages(self):
        if not self._audio_languages:
            # Get languages from the title
            filename_split = self.display_name.upper().split(" ")

            for code in filename_split:
                converted_code = ManageTitles.convert_iso(code)
                if converted_code:
                    self._audio_languages.append(converted_code[0])

            if not self._audio_languages:
                # get from the audio track
                self._audio_languages = self.languages
        return self._audio_languages

    @property
    def subtitle(self):
        if not self._subtitle:
            self._subtitle = self.guess_filename.subtitle
        return self._subtitle

    @property
    def torrent_path(self) -> str:
        if not self._torrent_path:
            self._torrent_path = os.path.join(self.folder, self.subfolder)
        return self._torrent_path

    @property
    def category(self):
        if self._category:
            return self._category

        # Check for ext file
        if ManageTitles.media_docu_type(self.title):
            self._category = System.category_list.get(System.DOCUMENTARY)
            return self._category

        # Search for a tv_show
        elif self.guess_filename.guessit_season:
            self._category = System.category_list.get(System.TV_SHOW)
        else:
            self._category = System.category_list.get(System.MOVIE)

        # If there's a crew or platform list -> game
        if self.crew_list or self.platform_list:
            self._category = System.category_list.get(System.GAME)
        return self._category

    @category.setter
    def category(self, value):
        self._category = value

    @property
    def mediafile(self):
        if not self._media_file:
            if self.category in {
                System.category_list.get(System.MOVIE),
                System.category_list.get(System.TV_SHOW),
            }:
                # Read from the current video file the height field
                file_path = os.path.join(self.folder, self.file_name)
                # Media file
                self._media_file = MediaFile(file_path)
        return self._media_file

    @property
    def languages(self):
        if not self._languages:
            self._languages = self.mediafile.available_languages
        return self._languages

    @staticmethod
    def resolution_from_size(width: int, height: int | None, interlaced: bool = False) -> str:
        """
        The resolution of a video from its width and height (RESOLUTION_THRESHOLDS), the height under 576p.
        An interlaced video is 1080i, 576i or 480i (INTERLACED_RESOLUTIONS)
        """
        resolution = next((resolution for resolution, min_width, min_height in RESOLUTION_THRESHOLDS
                           if width >= min_width or (height and height >= min_height)), f"{height}p")
        return INTERLACED_RESOLUTIONS.get(resolution, resolution) if interlaced else resolution

    @property
    def _resolution2(self):
        if self.mediafile:
            try:
                width = int(self.mediafile.video_width)
            except ValueError:
                print(f"{self.file_name} Video width unknown or file corrupted")
                exit()
            if self.mediafile.video_width:
                try:
                    height = int(self.mediafile.video_height)
                except (TypeError, ValueError):
                    height = None
                interlaced = str(self.mediafile.video_scan_type or "").lower() in INTERLACED_SCAN_TYPES
                return self.resolution_from_size(width, height, interlaced)
        return None

    @property
    def resolution(self):
        if not self._resolution:
            if self.mediafile:
                if self.mediafile.video_width:
                    self._resolution = self._resolution2
                else:
                    custom_console.bot_error_log(
                        f"'{self.__class__.__name__}' Video Height resolution not found in {self.file_name}"
                    )
                    custom_console.bot_error_log(
                        f"'{self.__class__.__name__}' Set to default value {System.NO_RESOLUTION}"
                    )
                    self._resolution = System.NO_RESOLUTION
            else:
                # Game
                self._resolution = System.NO_RESOLUTION

        return self._resolution

    @staticmethod
    def _crew(filename: str) -> list[str]:
        # Get the crew name only if the substr is at end of the string
        crew_regex = (
                r"\b(" + "|".join(re.escape(pattern) for pattern in crew_patterns) + r")\b$"
        )
        return re.findall(crew_regex, filename, re.IGNORECASE)

    @staticmethod
    def _platform(filename: str) -> list[str]:

        # Get the platform name
        platform_regex = (
                r"\b("
                + "|".join(re.escape(pattern) for pattern in platform_patterns)
                + r")\b"
        )
        platform_list = re.findall(platform_regex, filename, re.IGNORECASE)

        # Remove the platform string from the name
        return platform_list
