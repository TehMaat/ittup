# -*- coding: utf-8 -*-

from pathlib import Path
import argparse
import os
import math
import time
import shutil

from ittup.core.media import Media
from ittup.core.media_manager.ContentManager import ContentManager
from ittup.core.media_manager.TorrentManager import TorrentManager

from ittup.common.external_services.ftpx.core.models.list import FTPDirectory
from ittup.common.external_services.ftpx.core.menu import Menu
from ittup.common.external_services.ftpx.client import Client
from ittup.common.extractor import Extractor

from ittup.view import custom_console


class Bot:
    """
    A Bot class that manages media files, including processing, torrent management,TMDB ,FTP

    Methods:
        run(): Starts the media processing and torrent handling tasks
        watcher(duration: int, watcher_path: str): Monitors a folder for changes and processes files
        ftp(): Connects to a remote FTP server and processes files
    """

    # Bot Manager
    def __init__(self, path: str, cli: argparse.Namespace, trackers_name_list: list, tags_list = None, mode="man",
                 torrent_archive_path = None, sign_list= None, ban_list= None):
        """
        Initializes the Bot instance with path, command-line interface object, and mode

        Args:
            path (str): The path to the directory or file to be managed
            cli (argparse.Namespace): The command-line arguments object
            mode (str): The mode of operation, default is 'man'
        """
        self.trackers_name_list = trackers_name_list
        self.torrent_archive_path = torrent_archive_path
        self.content_manager = None
        self.tags_list: dict = tags_list
        self.sign_list: dict = sign_list
        self.ban_list: dict = ban_list
        self.path = path.strip()
        self.cli = cli
        self.mode = mode


    def contents(self, include_paths: list[str] | None = None) -> bool | list[Media]:
        """
        Start the process of analyzing and processing media files
        This method retrieves media files

        Args:
            include_paths: if set, only the media with these paths are processed
        """
        custom_console.panel_message("Analyzing your media files... Please wait")

        # Check permission
        try:
            os.stat(self.path)
        except PermissionError:
            custom_console.bot_error_log(f"Permission denied: {self.path}")
            return False
        except FileNotFoundError:
            custom_console.bot_error_log(f"Path not found: {self.path}")
            return False

        # Get a Files list with basic attributes and create a content object for each
        self.content_manager: ContentManager = ContentManager(path=self.path, mode=self.mode, cli=self.cli,
                                                              include_paths=include_paths)
        contents = self.content_manager.process()

        # -u requires a single file
        if not contents:
            custom_console.bot_error_log("There are no Media to process")
            return False

        # Print the list of files being processed
        custom_console.bot_process_table_log(contents)

        return contents


    def run(self, include_paths: list[str] | None = None) -> bool:
        """
        processes the files using the TorrentManager and SeedManager

        Args:
            include_paths: if set, only the media with these paths are processed
        """

        # Get the user content
        contents = self.contents(include_paths=include_paths)
        if not contents:
            return False

        # Instance a new run
        torrent_manager = TorrentManager(cli=self.cli, tracker_archive=self.torrent_archive_path,
                                         tags_list=self.tags_list, sign_list=self.sign_list, ban_list=self.ban_list)
        # Process the torrents content (files)
        torrent_manager.process(contents=contents)

        # We want to reseed
        if self.cli.reseed:
            torrent_manager.reseed(trackers_name_list=self.trackers_name_list)
        else:
            # otherwise run the torrents creations and the upload process
            torrent_manager.run(trackers_name_list=self.trackers_name_list)
        return True


    def watcher(self, duration: int, watcher_path: str,  destination_path: str)-> bool:
        """
        Monitors the watcher path for new files, moves them to the destination folder,
        then uploads them to the tracker

        Each cycle takes a snapshot of the watcher folder, waits 'duration' seconds and takes a second one.
        Only the entries whose size did not change between the two snapshots are moved (a file still
        being copied is left for the next cycle) and only the moved entries are processed

        Args:
            duration (int): The time duration in seconds for the watchdog to wait before checking again
            watcher_path (str): The path to the folder being monitored for new files
            destination_path: The destination path for the new files
        """
        self.path = str(destination_path)
        watcher_path = Path(watcher_path)
        destination = Path(destination_path)
        try:
            # Watchdog loop
            while True:
                # Return if the watcher path doesn't exist
                if not watcher_path.exists():
                    custom_console.bot_error_log("Watcher path does not exist or is not configured\n")
                    return False

                # First check
                previous_snapshot = self._snapshot(watcher_path)

                print()
                # Counter
                end_time = time.perf_counter() + duration
                while (remaining_time := end_time - time.perf_counter()) > 0:
                    custom_console.bot_counter_log(
                        f"WATCHDOG: {math.ceil(remaining_time)} seconds Ctrl-c to Exit "
                    )
                    time.sleep(min(1.0, remaining_time))
                print()

                # Second check
                current_snapshot = self._snapshot(watcher_path)

                # Skip if there are no files in the watcher folder
                if not current_snapshot:
                    custom_console.bot_log("The are no files in the Watcher folder\n")
                    continue

                # Move only the entries whose size is unchanged since the previous check
                moved_paths = []
                for name, signature in current_snapshot.items():
                    src = watcher_path / name
                    if previous_snapshot.get(name) != signature:
                        custom_console.bot_log(f"'{name}' is still being copied. Wait for the next cycle")
                        continue

                    dest = destination / name
                    # Limit the length of file paths printed
                    limiter_src = '...' if len(str(src)) > 50 else ''
                    limiter_dest = '...' if len(str(dest)) > 50 else ''
                    custom_console.bot_log(
                        f"{str(src)[:50]}{limiter_src} -> from 'watch folder' to 'destination folder'"
                        f" -> {str(dest)[:50]}{limiter_dest}"
                    )
                    try:
                        self._move(src, dest)
                    except OSError as e:
                        custom_console.bot_error_log(e)
                        continue
                    moved_paths.append(os.path.normpath(dest))

                if not moved_paths:
                    continue

                # Start uploading only the new files
                print()
                self.run(include_paths=moved_paths)

        except KeyboardInterrupt:
            custom_console.bot_log("Exiting...")
        return True

    @staticmethod
    def _snapshot(watcher_path: Path) -> dict[str, tuple]:
        """
        Returns a signature for each entry of the watcher folder: the file size or, for a folder,
        the relative path and size of each file it contains
        """
        snapshot = {}
        try:
            entries = list(watcher_path.iterdir())
        except OSError as e:
            custom_console.bot_error_log(e)
            return snapshot

        for entry in entries:
            try:
                if entry.is_dir():
                    snapshot[entry.name] = tuple(sorted(
                        (str(file.relative_to(entry)), file.stat().st_size)
                        for file in entry.rglob("*") if file.is_file()
                    ))
                else:
                    snapshot[entry.name] = (entry.stat().st_size,)
            except OSError:
                # The entry changed while we were reading it: wait for the next cycle
                continue
        return snapshot

    @staticmethod
    def _move(src: Path, dest: Path) -> None:
        """
        Moves a file or a folder to dest. A folder is merged into dest if it already exists
        """
        if src.is_dir() and dest.is_dir():
            for root, dirs, files in os.walk(src, topdown=False):
                dest_root = dest / Path(root).relative_to(src)
                dest_root.mkdir(parents=True, exist_ok=True)
                for file_name in files:
                    shutil.move(str(Path(root) / file_name), str(dest_root / file_name))
                # Remove the empty source directory
                os.rmdir(root)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))


    def ftp(self)-> None:
        """
        Connects to a remote FTP server and interacts with files.

        This method handles FTP connection, navigation, and file download from the remote server
        """
        custom_console.bot_question_log("\nConnecting to the remote FTP...\n")

        # FTP service
        ftp_client = Client()
        custom_console.bot_question_log(f"Connected to {ftp_client.sys_info()}\n\n")

        menu = Menu()

        page = ftp_client.home_page()
        menu.show(table=page)

        while True:
            user_option = ftp_client.user_input()
            page = ftp_client.input_manager(user_option)
            if page == 0:
                ftp_client.quit()
                break
            if not page:
                continue

            # Display selected folder or file
            if isinstance(page, FTPDirectory):
                ftp_directory_name = page.name
                if page.type == "Folder":
                    page = ftp_client.change_path(selected_folder=ftp_directory_name)
                    menu.show(table=page)
                else:
                    ftp_client.select_file(one_file_selected=page)
                continue

            # Show page as table
            menu.show(table=page)

        if ftp_client.download_to_local_path:
            self.path = os.path.dirname(ftp_client.download_to_local_path)
            self.mode = 'folder'
            # Upload -f process
            # Decompress .rar files if the flags are set
            extractor = Extractor(compressed_media__path=self.path)
            result = extractor.unrar()
            if result is False:
                custom_console.bot_error_log("Unrar Exit")
                exit(1)

            self.run()
        return None