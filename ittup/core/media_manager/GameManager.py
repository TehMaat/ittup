# -*- coding: utf-8 -*-
from argparse import Namespace
import os

from ittup.common.external_services.igdb.client import IGDBClient
from ittup.common.bittorrent import BittorrentData

from ittup.core.media_manager.common import UserContent
from ittup.core.upload import UploadBot
from ittup.core import config_settings
from ittup.core.media import Media

from ittup.view import custom_console

class GameManager:

    def __init__(self, contents: list["Media"], cli: Namespace):
        """
        Initialize the GameManager with the given contents

        Args:
            contents (list): List of content media objects
            cli (argparse.Namespace): user flag Command line
        """
        self.contents: list[Media] = contents
        self.cli: Namespace = cli
        self.igdb = IGDBClient()
        self.igdb_logged: bool = False

    def process(self, selected_tracker: str, tracker_name_list: list,  tracker_archive: str) -> list[BittorrentData]:
        """
        Process the game contents to filter duplicates and create torrents

        Returns:
            list: List of Bittorrent objects created for each content
        """

        # No games, no IGDB login
        if not self.contents:
            return []

        if self.cli.upload:
            custom_console.bot_error_log("Game upload works only with the '-f' flag.You need to specify a folder name.")
            return []


        #  Init the torrent list
        bittorrent_list = []
        for content in self.contents:
            # get the archive path
            archive = os.path.join(tracker_archive, selected_tracker)
            os.makedirs(archive, exist_ok=True)
            torrent_filepath = os.path.join(tracker_archive,selected_tracker, f"{content.torrent_name}.torrent")

            # Skip the old uploads
            if self.cli.watcher and os.path.exists(torrent_filepath):
                custom_console.bot_log(f"Watcher Active.. skip the old upload '{content.file_name}'")
                continue

            torrent_response = UserContent.torrent(content=content, tracker_name_list=tracker_name_list,
                                                       selected_tracker=selected_tracker, this_path=torrent_filepath)


            # Skip if it is a duplicate
            if ((self.cli.duplicate or config_settings.user_preferences.DUPLICATE_ON)
                    and UserContent.is_duplicate(content=content, tracker_name=selected_tracker, cli=self.cli)):
                continue

            # Login to IGDB only when the first game needs it
            if not self.igdb_logged:
                if not self.igdb.connect():
                    exit(1)
                self.igdb_logged = True

            # Search for the game on IGDB using the content's title and platform tags
            game_data_results = self.igdb.game(content=content)
            # print the title will be shown on the torrent page
            custom_console.bot_log(f"'DISPLAYNAME'...{{{content.display_name}}}\n")

            # Skip the upload if there is no valid IGDB
            if not game_data_results:
                continue

            # Tracker instance
            unit3d_up = UploadBot(content=content, tracker_name=selected_tracker, cli = self.cli)

            # Get the data
            unit3d_up.data_game(igdb=game_data_results)

            # Don't upload if -noup is set to True
            if self.cli.noup:
                custom_console.bot_warning_log(f"No Upload active. Done.")
                continue

            # Send to the tracker
            tracker_response, tracker_message = unit3d_up.send(torrent_archive=torrent_filepath, nfo_path=content.game_nfo)

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
                UserContent.send_to_bittorrent([bittorrent_data], 'GAME')
        return bittorrent_list

