# -*- coding: utf-8 -*-
from argparse import Namespace
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
import os
import unicodedata

from ittup.common.external_services.theMovieDB.core.api import DbOnline
from ittup.common.bittorrent import BittorrentData
from ittup.common.frames import VideoFrame
from ittup.common.integrity import MediaIntegrity, MIN_FFPROBE_VERSION, UnsupportedFFprobe
from ittup.common.tags import SearchTags
from ittup.common.rename import rename_to_title
from ittup.common.utility import ManageTitles, System
from ittup.common import title

from ittup.core.media_manager.common import UserContent
from ittup.core.upload import UploadBot
from ittup.core import config_settings
from ittup.core.pvtVideo import Video
from ittup.core.media import Media
from ittup.core.report import report

from ittup.view import custom_console


class VideoManager:

    def __init__(self, contents: list[Media], cli: Namespace, tags_list: dict, sign_list: dict, ban_list: dict,
                 on_upload: Callable[[BittorrentData], None] | None = None):
        """
        Initialize the VideoManager with the given contents

        Args:
            contents (list): List of content media objects
            cli (argparse.Namespace): user flag Command line
            on_upload: if set, called with each uploaded torrent right after the upload
        """

        self.torrent_found: bool = False
        self.contents: list[Media] = contents
        self.cli: Namespace = cli
        self.tags_list: dict = tags_list
        self.sign_list: dict = sign_list
        self.ban_list: dict = ban_list
        self.on_upload = on_upload
        self.screenshots_executor: ThreadPoolExecutor | None = None

    @staticmethod
    def rename_files(content: Media) -> None:
        """
        Rename the file, or the folder and its video files, as the title shown on the tracker (RENAME_FILES)
        The episodes of a pack take their SxxExx. A complete name is kept or only gets the missing source
        """
        path = content.torrent_path
        video_files, episodes, pack = [], {}, None
        if os.path.isdir(path):
            video_files = sorted([file for file in os.listdir(path) if ManageTitles.filter_ext(file)],
                                 key=System.natural_key)
            if content.torrent_pack:
                pack = content.pack
                for file in video_files:
                    guess = title.Guessit(ManageTitles.clean_text(file))
                    episode = guess.guessit_episode
                    # A file with more episodes keeps its name
                    episodes[file] = (guess.guessit_season or content.guess_season,
                                      episode if isinstance(episode, int) else None)

        new_path, renamed_files = rename_to_title(path=path, display_name=content.display_name,
                                                  video_files=video_files, pack=pack, episodes=episodes,
                                                  info=content.title_info)
        if new_path != path or renamed_files:
            content.renamed(path=new_path, renamed_files=renamed_files)

    def extract_screenshots(self, content: Media) -> Future[tuple[list[bytes], int]] | None:
        """
        Start extracting the screenshots in the background, while the torrent is hashed

        :return: the screenshots, None if they are extracted later by Video
        """
        # A cached description doesn't need the screenshots, and a renamed file can't be read by ffmpeg
        if config_settings.user_preferences.CACHE_SCR or config_settings.user_preferences.RENAME_FILES:
            return None
        video_frames = VideoFrame(content.file_name, num_screenshots=Video.screenshots_number())
        return self.screenshots_executor.submit(video_frames.create)

    @staticmethod
    def corrupted(content: Media) -> bool:
        """
        True if the file, or a video file of the folder, is corrupted (CHECK_CORRUPTED)
        """
        preferences = config_settings.user_preferences
        try:
            errors, ignored = MediaIntegrity.check(content.torrent_path, preferences.CHECK_CORRUPTED_START,
                                                   preferences.CHECK_CORRUPTED_END,
                                                   preferences.CHECK_CORRUPTED_IGNORE_DV)
        except FileNotFoundError:
            custom_console.bot_error_log("[FFMPEG-ffprobe not found] - Install ffmpeg or check your system path")
            exit(1)
        except UnsupportedFFprobe as version:
            custom_console.bot_error_log(f"[FFMPEG-ffprobe too old] - '{version}': the corrupted files check needs "
                                         f"ffprobe {'.'.join(map(str, MIN_FFPROBE_VERSION))} or newer. "
                                         f"Update ffmpeg or set CHECK_CORRUPTED to False")
            exit(1)

        for file, error in ignored.items():
            custom_console.bot_warning_log(f"Dolby Vision metadata error ignored in '{os.path.basename(file)}' "
                                           f"(CHECK_CORRUPTED_IGNORE_DV): {error}")
        for file, error in errors.items():
            custom_console.bot_error_log(f"Corrupted file '{os.path.basename(file)}': {error}")
        if errors:
            custom_console.bot_error_log(f"Skip the upload of '{content.display_name}'")
            custom_console.rule()
            report.failed(content.display_name, "corrupted file: " + "; ".join(
                f"{os.path.basename(file)}: {error}" for file, error in errors.items()))
        return bool(errors)

    @staticmethod
    def italian_title(details: dict | None) -> str | None:
        """
        Title (movie) or name (tv show) in Italian from the TMDB details, None if it is unknown
        """
        if not details:
            return None
        italian = (details.get('title') or details.get('name') or '').strip()
        # Without an Italian translation TMDB returns the original title: skip it if it is not in latin script
        if any(char.isalpha() and not unicodedata.name(char, '').startswith('LATIN') for char in italian):
            return None
        return italian or None

    @staticmethod
    def full_season(pack: str | None, details: dict | None) -> str | None:
        """
        'Sxx' when the episode pack has every episode of a season that TMDB has concluded, otherwise None
        """
        episodes = ManageTitles.pack_episodes(pack)
        if not episodes or not details:
            return None
        season, first, last = episodes

        # The season goes on: TMDB already knows its next episode
        next_episode = details.get('next_episode_to_air') or {}
        if next_episode.get('season_number') == season:
            return None

        episode_count = next((item.get('episode_count') for item in details.get('seasons') or []
                              if item.get('season_number') == season), None)
        if episode_count and first == 1 and last >= episode_count:
            return f"S{season:02d}"
        return None

    def check(self, content: Media, selected_tracker: str, archive: str):
        """
        Build the final title of the content and check it for duplicates on the tracker

        :return: the TMDB result, None if the content is skipped
        """
        # Skip the old uploads before reading guessit, mediainfo and tags
        if self.cli.watcher and os.path.exists(os.path.join(archive, f"{content.torrent_name}.torrent")):
            custom_console.bot_log(f"Watcher Active.. skip the old upload '{content.file_name}'")
            return None

        # /// User request to build the title; overwriting display_name
        guess_filename = title.Guessit(content.title_sanitize_tags)
        guess = guess_filename.guessit
        tags_position = config_settings.user_preferences.TAGS_POSITION_SERIE if content.category=='tv'\
            else config_settings.user_preferences.TAGS_POSITION_MOVIE
        search_tags = SearchTags(filename=content.title,
                                 # Keep the special characters of the title ('Spider-Man', 'Mission: Impossible')
                                 title=ManageTitles.original_spelling(guess.get("title", None), content.title),
                                 year=guess.get("year", ""),
                                 season=content.guess_season,
                                 episode=content.guess_episode,
                                 releaser_sign=config_settings.user_preferences.RELEASER_SIGN,
                                 tags_position=tags_position,
                                 tags_list=self.tags_list,
                                 sign_list=self.sign_list,
                                 ban_list=self.ban_list,
                                 media=content,
                                 )
        content.display_name, _ = search_tags.process()
        if search_tags.mediainfo_tags:
            content.mediainfo_source = " ".join(sum(search_tags.mediainfo_tags.values(), []))

        # Filter contents based on the preferred language
        if not UserContent.is_preferred_language(content=content):
            return None

        # Search for VIDEO ID
        db_online = DbOnline(media=content, category=content.category, no_title=self.cli.notitle)
        db = db_online.media_result

        # If it is 'None' we skipped the imdb search (-notitle)
        if not db:
            report.failed(content.display_name, "not found on TMDB")
            return None

        # The audio tags need the original language from TMDB
        content.display_name, _ = search_tags.set_original_language(db.original_language)

        # Details in Italian from TMDB
        details = db_online.italian_details(video_id=db.video_id, category=content.category)

        # The title in Italian from TMDB, with its punctuation
        italian_title = self.italian_title(details)
        if italian_title:
            content.display_name, _ = search_tags.set_title(italian_title)

        # A pack with every episode of a concluded season is the season: S04E01-10 -> S04
        season_pack = self.full_season(pack=content.pack, details=details)
        if season_pack:
            custom_console.bot_log(f"'{content.pack}' is the whole season on TMDB: '{season_pack}'")
            content.pack = season_pack
            content.display_name, _ = search_tags.set_season(season_pack)

        # What the file names should say, for RENAME_FILES
        content.title_info = search_tags.title_info()

        # Skip(S) if it is a duplicate or let the user choose to continue (C)
        # Checked with the final title and before hashing, so a skipped duplicate doesn't cost a torrent file
        if ((self.cli.duplicate or config_settings.user_preferences.DUPLICATE_ON)
                and UserContent.is_duplicate(content=content, tracker_name=selected_tracker, cli=self.cli,
                                             tmdb_id=db.video_id)):
            return None
        return db

    def process(self, selected_tracker: str, tracker_name_list: list, tracker_archive: str) -> list[BittorrentData]:
        """
           Process the video contents to filter duplicates and create torrents
           Every content is checked for duplicates first, so the questions to the user come before
           the screenshots, the torrent files and the uploads

           Returns:
               list: List of Bittorrent objects created for each content
        """

        #  Init the torrent list
        bittorrent_list = []
        # get the archive path
        archive = os.path.join(tracker_archive, selected_tracker)
        os.makedirs(archive, exist_ok=True)

        # The titles, TMDB and the duplicates of every content
        checked = []
        for content in self.contents:
            db = self.check(content=content, selected_tracker=selected_tracker, archive=archive)
            if db:
                checked.append((content, db))

        # One content at a time: the screenshots are extracted while the torrent is hashed
        self.screenshots_executor = ThreadPoolExecutor(max_workers=1)
        for content, db in checked:
            # Skip the corrupted video files: ffprobe reads the container and decodes a few frames
            if config_settings.user_preferences.CHECK_CORRUPTED and self.corrupted(content):
                continue

            screenshots = self.extract_screenshots(content)

            # Rename the original files as the title shown on the tracker before creating the torrent
            if config_settings.user_preferences.RENAME_FILES:
                self.rename_files(content=content)
            torrent_filepath = os.path.join(archive, f"{content.torrent_name}.torrent")

            torrent_response = UserContent.torrent(content=content, tracker_name_list=tracker_name_list,
                                                   selected_tracker=selected_tracker, this_path=torrent_filepath)

            # Get meta from the media video
            video_info = Video(media=content, tmdb_id=db.video_id, trailer_key=db.trailer_key,
                               screenshots=screenshots)
            video_info.build_info()

            # Print the title shown on the torrent page on a single line
            custom_console.bot_log(f"\n[GENERATING DISPLAYNAME..]")
            custom_console.bot_log(f"'{content.display_name}'")
            custom_console.bot_log(f"Done.\n")

            # Tracker instance
            unit3d_up = UploadBot(content=content, tracker_name=selected_tracker, cli=self.cli)

            # Get the data
            processed_data = unit3d_up.data(show_id=db.video_id, imdb_id=db.imdb_id, tvdb_id=db.tvdb_id,
                           show_keywords_list=db.keywords_list, video_info=video_info)

            # Do not upload if an error occurs
            if not processed_data:
                report.failed(content.display_name, f"resolution '{content.resolution}' or category"
                                                    f" '{content.category}' unknown to the tracker")
                continue

            # Don't upload if -noup is set to True
            if self.cli.noup:
                custom_console.bot_warning_log(f"No Upload active. Done.")
                continue

            # Send to the tracker
            tracker_response, tracker_message = unit3d_up.send(torrent_archive=torrent_filepath)

            # Store response for the torrent clients
            bittorrent_list.append(
                BittorrentData(
                    tracker_response=tracker_response,
                    torrent_response=torrent_response,
                    content=content,
                    tracker_message=tracker_message,
                    archive_path=torrent_filepath,
                ))

            # Send the torrent to the client as soon as it is uploaded
            if self.on_upload:
                self.on_upload(bittorrent_list[-1])

        # // end content
        self.screenshots_executor.shutdown(wait=False, cancel_futures=True)
        return bittorrent_list
