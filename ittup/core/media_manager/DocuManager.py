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
        # get the archive path
        archive = os.path.join(tracker_archive, selected_tracker)
        os.makedirs(archive, exist_ok=True)

        # Every content is checked for duplicates before the first torrent file
        contents = UserContent.not_duplicates(contents=self.contents, tracker_name=selected_tracker,
                                              archive=archive, cli=self.cli)
        for content in contents:
            torrent_filepath = os.path.join(archive, f"{content.torrent_name}.torrent")

            torrent_response = UserContent.torrent(content=content, tracker_name_list=tracker_name_list,
                                                   selected_tracker=selected_tracker, this_path=torrent_filepath)

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

        return bittorrent_list