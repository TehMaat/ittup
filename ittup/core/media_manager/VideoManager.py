# -*- coding: utf-8 -*-
from argparse import Namespace
import os

from ittup.common.external_services.theMovieDB.core.api import DbOnline
from ittup.common.bittorrent import BittorrentData
from ittup.common.tags import SearchTags
from ittup.common import title

from ittup.core.media_manager.common import UserContent
from ittup.core.upload import UploadBot
from ittup.core import config_settings
from ittup.core.pvtVideo import Video
from ittup.core.media import Media

from ittup.view import custom_console


class VideoManager:

    def __init__(self, contents: list[Media], cli: Namespace, tags_list: dict, sign_list: dict, ban_list: dict):
        """
        Initialize the VideoManager with the given contents

        Args:
            contents (list): List of content media objects
            cli (argparse.Namespace): user flag Command line
        """

        self.torrent_found: bool = False
        self.contents: list[Media] = contents
        self.cli: Namespace = cli
        self.tags_list: dict = tags_list
        self.sign_list: dict = sign_list
        self.ban_list: dict = ban_list

    def process(self, selected_tracker: str, tracker_name_list: list, tracker_archive: str) -> list[BittorrentData]:
        """
           Process the video contents to filter duplicates and create torrents

           Returns:
               list: List of Bittorrent objects created for each content
        """

        #  Init the torrent list
        bittorrent_list = []
        # Tags list extracted used to build title ( -b flag)
        tags_dictionary = {}
        for content in self.contents:
            # get the archive path
            archive = os.path.join(tracker_archive, selected_tracker)
            os.makedirs(archive, exist_ok=True)
            torrent_filepath = os.path.join(tracker_archive, selected_tracker, f"{content.torrent_name}.torrent")

            # Skip the old uploads before reading guessit, mediainfo and tags
            if self.cli.watcher and os.path.exists(torrent_filepath):
                custom_console.bot_log(f"Watcher Active.. skip the old upload '{content.file_name}'")
                continue

            # /// User request to build the title; overwriting display_name
            guess_filename = title.Guessit(content.title_sanitize_tags)
            guess = guess_filename.guessit
            tags_position = config_settings.user_preferences.TAGS_POSITION_SERIE if content.category=='tv'\
                else config_settings.user_preferences.TAGS_POSITION_MOVIE
            search_tags = SearchTags(filename=content.title,
                                     title=guess.get("title", None),
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
            content.display_name, tags_dictionary = search_tags.process()

            # Filter contents based on the preferred language or duplicates
            if UserContent.is_preferred_language(content=content):

                torrent_response = UserContent.torrent(content=content, tracker_name_list=tracker_name_list,
                                                       selected_tracker=selected_tracker, this_path=torrent_filepath)

                # Skip(S) if it is a duplicate or let the user choose to continue (C)
                if ((self.cli.duplicate or config_settings.user_preferences.DUPLICATE_ON)
                        and UserContent.is_duplicate(content=content, tracker_name=selected_tracker,
                                                     cli=self.cli)):
                    continue

                # Search for VIDEO ID
                db_online = DbOnline(media=content, category=content.category, no_title=self.cli.notitle)
                db = db_online.media_result

                # If it is 'None' we skipped the imdb search (-notitle)
                if not db:
                    continue

                # Get meta from the media video
                video_info = Video(media=content, tmdb_id=db.video_id, trailer_key=db.trailer_key)
                video_info.build_info()

                # Tags found ( -b flag)
                if tags_dictionary:
                    custom_console.bot_log(f"\n[GENERATING DISPLAYNAME..]")
                    for key, value in tags_dictionary.items():
                        if isinstance(value, list):
                            value = " ".join(value)
                        custom_console.bot_log(f"{key:<13} '{value}'")
                    custom_console.bot_log(f"Done.\n")
                else:
                    # print the title will be shown on the torrent page
                    custom_console.bot_log(f"'DISPLAYNAME'...{{{content.display_name}}}\n")

                # Tracker instance
                unit3d_up = UploadBot(content=content, tracker_name=selected_tracker, cli=self.cli)

                # Get the data
                processed_data = unit3d_up.data(show_id=db.video_id, imdb_id=db.imdb_id, tvdb_id=db.tvdb_id,
                               show_keywords_list=db.keywords_list, video_info=video_info)

                # Do not upload if an error occurs
                if not processed_data:
                    continue

                # Don't upload if -noup is set to True
                if self.cli.noup:
                    custom_console.bot_warning_log(f"No Upload active. Done.")
                    continue

                # Send to the tracker
                tracker_response, tracker_message = unit3d_up.send(torrent_archive=torrent_filepath)

                # Store response for the torrent clients
                bittorrent_data = BittorrentData(
                    tracker_response=tracker_response,
                    torrent_response=torrent_response,
                    content=content,
                    tracker_message=tracker_message,
                    archive_path=torrent_filepath,
                )
                bittorrent_list.append(bittorrent_data)

                # Seed it right away, without waiting for the other contents
                if not self.cli.noseed:
                    UserContent.send_to_bittorrent([bittorrent_data], 'VIDEO')

        # // end content
        return bittorrent_list
