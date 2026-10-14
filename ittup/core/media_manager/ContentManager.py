# -*- coding: utf-8 -*-
import argparse
import json
import os
import re

from ittup.common.utility import ManageTitles, System
from ittup.core.automode import Auto
from ittup.core.media import Media

# {tmdb-603}, [tmdbid-603], [tmdbid=603], (tmdb-603), tmdb 603, {imdb-tt0133093}..
ID_PATTERN = re.compile(r"[\[{(]?(?<![a-z0-9])(imdb|tmdb|tvdb|igdb)(?:id)?\s*[-=:\s]\s*(tt)?(\d+)(?![0-9])\s*[\]})]?",
                        re.IGNORECASE)
# IMDB ID alone: tt0133093
IMDB_PATTERN = re.compile(r"(?<![a-z0-9])tt(\d{7,8})(?![0-9])", re.IGNORECASE)


class ContentManager:
    def __init__(self, path: str, mode: str, cli: argparse.Namespace, include_paths: list[str] | None = None):
        """
        Args:
            path (str): The path to the media files or directories
            mode (str):  mode 'manual' or 'automatic'
            include_paths (list): if set, keep only the media with these paths (watcher)
        """
        self.path = path
        self.mode = mode
        self.cli = cli

        self.languages: list[str] | None = None
        self.display_name: str | None = None
        self.meta_info_list: list[dict] = []
        self.game_nfo: str = ''
        self.category: int | None = None

        self.meta_info: str | None = None
        self.size: int | None = None
        self.torrent_name: str | None = None
        self.folder: str | None = None
        self.file_name: str | None = None
        self.torrent_path: str | None = None
        self.doc_description: str | None = None
        self.tmdb_id: int  = 0
        self.imdb_id: int  = 0
        self.tvdb_id: int  = 0
        self.igdb_id: int  = 0
        self.generate_title: str | None = None

        self.path: str = os.path.normpath(path)
        self.auto = Auto(path=self.path, mode=self.mode)
        self.media_list = self.auto.upload() if self.mode in ["man", "folder"] else self.auto.scan()
        if include_paths is not None:
            include = {os.path.normpath(p) for p in include_paths}
            self.media_list = [media for media in self.media_list
                               if os.path.normpath(media.torrent_path) in include]

    def process(self)-> list[Media]:
        contents = []
        for media in self.media_list:
            self.path = media.torrent_path
            media.category = media.category if not self.cli.force else self.cli.force
            self.category = media.category

            content = self.get_data(media=media)
            if content:
                contents.append(content)
        return contents

    def get_data(self, media: Media) -> Media | bool:
        """
        Process files or folders and create a `Contents` object if the metadata is valid
        """
        process = False
        if os.path.isdir(self.path):
            process = self.process_folder()
        elif os.path.isfile(self.path):
            process = self.process_file()

        if not self.meta_info:
            return False

        # add category filter to the regex result caused by a possible substring (e.g., S06) in the whole path
        # and not part of the title
        pack = ManageTitles.season_pack(self.path) if media.category == 'tv' else None
        torrent_pack = bool(pack)

        if process:
            media.file_name = self.file_name
            media.torrent_name = self.torrent_name
            media.size = self.size
            media.torrent_pack = torrent_pack
            media.pack = pack
            media.metainfo = self.meta_info
            media.doc_description = self.doc_description
            media.game_nfo = self.game_nfo

            # Add ID if there are one in the title
            media.imdb_id = self.imdb_id
            media.tvdb_id = self.tvdb_id
            media.tmdb_id = self.tmdb_id
            media.igdb_id = self.igdb_id
            media.display_name = self.display_name

            return media
        else:
            return False


    def search_ids(self):
        # Reset the IDs of the previous file: this instance processes every media in the list
        self.imdb_id = 0
        self.tmdb_id = 0
        self.tvdb_id = 0
        self.igdb_id = 0

        # e.g. {imdb-tt0133093} (Radarr/Sonarr/Plex naming), {imdb-0133093}, {tmdb-603},
        # [tmdbid-603] (Jellyfin), [tmdbid=603] (Emby), (tmdb-603), tmdb 603 or the IMDB ID alone (tt0133093)
        _id = ID_PATTERN.findall(self.file_name)
        for source, _, value in _id:
            setattr(self, f"{source.lower()}_id", value)
        imdb = IMDB_PATTERN.search(self.file_name)
        if imdb and not self.imdb_id:
            self.imdb_id = imdb.group(1)

        if _id or imdb:
            # The display name is already cleaned, so '{imdb-tt0133093}' may now read '{imdb tt0133093}'
            self.display_name = ID_PATTERN.sub('', self.display_name)
            self.display_name = IMDB_PATTERN.sub('', self.display_name)
            self.display_name = re.sub(r"\s{2,}", ' ', self.display_name).strip()

    def process_file(self) -> bool:
        """Process individual files and gather metadata"""
        self.file_name = self.path

        # # Display name on webpage
        self.display_name, _ = os.path.splitext(os.path.basename(self.file_name))
        self.display_name = ManageTitles.clean_text(self.display_name)
        self.display_name = re.sub(r'[\[\]()]', '', self.display_name)

        # current media path
        self.torrent_path = self.path
        # Try to get video ID from the string title
        self.search_ids()
        # Torrent name
        self.torrent_name =  os.path.basename(self.file_name)
        # test to check if it is a doc
        self.doc_description = self.file_name

        # Build meta_info
        self.size = os.path.getsize(self.path)
        self.meta_info = json.dumps([{"length": self.size, "path": [self.file_name]}], indent=4)
        return True

    def process_folder(self)-> bool:
        """Process folder and gather metadata for a torrent containing multiple files"""
        files_list = self.list_files_by_category()
        if not files_list:
            return False

        # Sample the first file in the list
        self.file_name = os.path.join(self.path, files_list[0])

        # # Display name on webpage
        self.display_name = ManageTitles.clean_text(os.path.basename(self.path))
        self.display_name = re.sub(r'[\[\]()]', '', self.display_name)

        # current media path
        self.torrent_path = self.path
        # Torrent name
        self.torrent_name = os.path.basename(self.path)
        # Document description
        self.doc_description = "\n".join(files_list)
        # Try to get video ID from the string title
        self.search_ids()
        # Build meta_info
        self.size = 0
        self.meta_info_list = []
        for file in files_list:
            size = os.path.getsize(os.path.join(self.path, file))
            self.meta_info_list.append({"length": size, "path": [file]})
            self.size += size
            if file.lower().endswith(".nfo"):
                self.game_nfo = os.path.join(self.path, file)

        self.meta_info = json.dumps(self.meta_info_list, indent=4)
        return True
    def list_files_by_category(self) -> list[str]:
        """List files based on the content category"""
        if self.category ==System.category_list.get(System.GAME):
            return self.list_game_files()
        return self.list_video_files()

    def list_video_files(self) -> list[str]:
        """List video files in the folder"""
        return sorted([file for file in os.listdir(self.path) if ManageTitles.filter_ext(file)], key=System.natural_key)

    def list_game_files(self) -> list[str]:
        """List all files in a game folder"""
        return sorted(os.listdir(self.path), key=System.natural_key)