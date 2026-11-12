# -*- coding: utf-8 -*-

import os
from ittup.common.utility import ManageTitles, System
from ittup.view import custom_console

from ittup.core.media import Media

class Auto:
    """
    A class for managing and processing video files and directories based on a given mode
    """

    def __init__(self, path: str, mode="auto"):
        """
        Initialize the Auto instance with path, tracker configuration, and mode.

        Args:
            path (str): The path to the directory or file to be processed.
            mode (str): The mode of operation, either 'auto', 'man', or 'folder'. Default is 'auto'.
        """

        self.series = None
        self.movies = None
        self.path = path
        self.is_dir = os.path.isdir(self.path)
        self.auto = mode

    def upload(self):
        """
        Handles the upload process based on the specified mode.

        If the path is a directory, it processes video files and directories according to the mode:
        - 'man': Single file or scan each file in the folder
        - 'folder': Single folder series or 'saga'
        If the path is not a directory, it processes the path as a single file
        """
        if self.is_dir:
            series_path = self.list_video_files(self.path)

            if self.auto == "man":
                # -u command (single file or scan each file in the folder)
                return self._lists(files_path=[], subfolders_path=series_path)

            if self.auto == "folder":
                # -f command (single folder series or 'saga')
                if self.season_folders(self.path):
                    # -f uploads the files of the folder, not the ones in its subfolders (#116)
                    custom_console.bot_error_log(
                        f"'{os.path.basename(self.path)}' has a folder for each season and no video file of its own: "
                        "upload one season at a time with -f <season folder>, or all of them with -scan")
                    return []
                return self._lists(files_path=[], subfolders_path=[self.path])
            return None
        else:
            return self._lists(files_path=[self.path], subfolders_path=[])

    def scan(self):
        """
        Scans the directory for video files and subdirectories.

        If the path is a file, logs an error since scanning requires a folder. Otherwise, scans
        the folder and subfolders, sorting files and subdirectories, and processes them
        """
        files_path = []
        subfolders_path = []

        if not self.is_dir:
            custom_console.bot_error_log("We can't scan a file.")
        else:
            # Scan folder and subfolders
            for path, sub_dirs, files in os.walk(self.path):
                # Sort subdirs
                sub_dirs.sort(reverse=False)
                # Sort files
                files.sort(reverse=False)

                # Get the files path from the self.path
                if path == self.path:
                    files_path = [
                        os.path.join(self.path, file)
                        for file in files
                        if ManageTitles.filter_ext(file)
                    ]
                # Get the subfolders path from the self.path
                if sub_dirs:
                    # Maximum level of subfolder depth = 1
                    if self.depth_walker(path) < 1:
                        subfolders_path = [
                            os.path.join(self.path, subdir) for subdir in sub_dirs
                        ]
            # A series with a folder for each season: a pack for each season (#116)
            subfolders_path = [season for folder in subfolders_path
                               for season in self.season_folders(folder) or [folder]]
        return self._lists(files_path=files_path, subfolders_path=subfolders_path)

    def _lists(self, files_path: list, subfolders_path: list):

        # Files and folders in alphanumeric order
        return [
            result
            for media_path in sorted(files_path + subfolders_path, key=System.natural_key)
            if (result := Media(folder=self.path,subfolder=media_path)) is not None
        ]


    def depth_walker(self, path) -> int:
        """
        Calculates the depth of a given path relative to the base path.

        Args:
            path (str): The path to evaluate.

        Returns:
            int: The depth level of the path, where depth < 1 indicates a maximum of one level of subfolders
        """
        return path[len(self.path):].count(os.sep)

    @staticmethod
    def season_folders(folder: str) -> list[str]:
        """
        The season folders of a series: the subfolders with a season in the name ('Show.S01..') and video
        files, when the folder has no video file of its own. Empty for any other folder
        """
        if Auto.list_video_files(folder):
            return []
        subfolders = (os.path.join(folder, name) for name in os.listdir(folder))
        return sorted((path for path in subfolders
                       if os.path.isdir(path) and ManageTitles.season_pack(os.path.basename(path))
                       and Auto.list_video_files(path)), key=System.natural_key)

    @staticmethod
    def list_video_files(manual_path: str) -> list:
        """
        Lists all video files in a given directory based on their extension

        Args:
            manual_path (str): The directory path to scan for video files

        Returns:
            list: A list of video files in the directory that match the video file extensions
        """
        return [
            file for file in os.listdir(manual_path) if ManageTitles.filter_ext(file)
        ]
