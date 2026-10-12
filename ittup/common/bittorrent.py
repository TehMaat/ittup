# -*- coding: utf-8 -*-

from dataclasses import dataclass
from ittup.core.pvtTorrent import Mytorrent
from ittup.core.media import Media


@dataclass
class BittorrentData:
    tracker_response: str
    torrent_response: Mytorrent | None
    content: Media
    tracker_message: dict
    archive_path: str
