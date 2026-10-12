# -*- coding: utf-8 -*-
from argparse import Namespace
from collections.abc import Callable
import os

from ittup.common.bittorrent import BittorrentData

from ittup.core.media_manager.common import UserContent
from ittup.core.pvtDocu import PdfImages
from ittup.core.upload import UploadBot
from ittup.core import config_settings
from ittup.core.media import Media

from ittup.view import custom_console

class DocuManager:

    def __init__(self, contents: list[Media], cli: Namespace,
                 on_upload: Callable[[BittorrentData], None] | None = None):
        self._my_tmdb = None
        self.contents: list['Media'] = contents
        self.cli: Namespace = cli
        # If set, called with each uploaded torrent right after the upload
        self.on_upload = on_upload

    def process(self, selected_tracker: str, tracker_name_list: list, tracker_archive: str) -> list[BittorrentData]:

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

            # print the title will be shown on the torrent page
            custom_console.bot_log(f"'DISPLAYNAME'...{{{content.display_name}}}\n")

            # Don't upload if -noup is set to True
            if self.cli.noup:
                custom_console.bot_warning_log(f"No Upload active. Done.")
                continue

            # Get the cover image
            docu_info = PdfImages(content.file_name)
            docu_info.build_info()


            # Tracker payload
            unit3d_up = UploadBot(content=content, tracker_name=selected_tracker, cli = self.cli)

            # Upload
            unit3d_up.data_docu(document_info=docu_info)

            # Get the data
            tracker_response, tracker_message = unit3d_up.send(torrent_archive=torrent_filepath)

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
                UserContent.send_to_bittorrent([bittorrent_data], 'DOCUMENTARY')

            # Send the torrent to the client as soon as it is uploaded
            if self.on_upload:
                self.on_upload(bittorrent_list[-1])

        return bittorrent_list