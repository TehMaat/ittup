# -*- coding: utf-8 -*-

import os
import re

from dataclasses import dataclass
from ittup.common.utility import ManageTitles
from ittup.common.trackers.tags_list import TAGS_LIST
from . import tracker_list

@dataclass
class TRACKData:
    category: dict[str, int]
    freelech: dict[str, int]
    type_id: dict[str, int]
    resolution: dict[str, int]
    codec: list

    @classmethod
    def load_from_module(cls, tracker_name: str) -> "TRACKData":
        """
        Load tracker data from module
        """
        tracker_data= tracker_list[tracker_name.upper()]

        return cls(
            category=tracker_data.get("CATEGORY"),
            freelech=tracker_data.get("FREELECH"),
            type_id=tracker_data.get("TYPE_ID"),
            resolution=tracker_data.get("RESOLUTION"),
            codec=tracker_data.get("CODEC"),
        )

    def filter_type(self, *names: str) -> int:
        """
        Tracker type ID from the release names (es. the folder name, then the file name)
        The first name with a source (WEB-DL, REMUX, WEBRip..) wins, so the type always follows the source
        written in the title. Without a source, a codec in the name means 'encode'
        """
        names = [os.path.basename(str(name)) for name in names if name]

        # Caso 1: Cerca la sorgente nel nome, dalla piu' importante
        for name in names:
            found = self.type_tags(name)
            if found:
                return self.type_id[min(found, key=type_priority)]

        # Caso 2: Se non trova un TYPE_ID, cerca un codec e ritorna 'encode'
        for name in names:
            word_list = ManageTitles.clean(name).replace("-", " ").lower().split(" ")
            if any(word in self.codec for word in word_list):
                return self.type_id.get("encode", -1)
        return self.type_id.get("altro", -1)

    def type_tags(self, name: str) -> list[str]:
        """
        TYPE_ID tags written in the name. A longer tag hides the shorter ones inside it (WEB-DLMux is not DLMux)
        """
        name = re.sub(r"[._\s()\[\]{}+,]+", " ", name.lower())
        # Skip the title: the tags start from the year, the season or the resolution ('Charlotte's Web 2006 BluRay')
        start = TITLE_END.search(name)
        if start and start.start() > 0:
            name = name[start.start():]
        # NFRip, AMZNRip.. are WEBRip from a streaming platform
        name = PLATFORM_RIP.sub("webrip", name)
        name = re.sub(r"(?<![a-z0-9])full disc(?![a-z0-9])", "full-disc", name)

        found = []
        for tag in sorted(self.type_id, key=len, reverse=True):
            # 'altro' is the default type, not a tag (es. 'Un altro giro')
            if tag == "altro":
                continue
            pattern = re.compile(rf"(?<![a-z0-9]){re.escape(tag)}(?![a-z0-9])")
            if pattern.search(name):
                found.append(tag)
                # Hide the matched tag from the shorter ones
                name = pattern.sub(" ", name)
        return found


# Type tags from the most to the least important: the release source before the generic tags
# (BluRay, HEVC, FullHD..) and before the file extensions. Tags not in the list come last
TYPE_PRIORITY = [
    "full-disc", "fulldisc",
    "bdmux", "web-dlmux", "dlmux", "webmux",
    "bd-untouched", "untouched", "bdremux", "remux", "vu", "vh",
    "web-dl", "webdl", "web",
    "webrip",
    "hdtv",
    "bdrip", "dvdrip",
    "cinema-md", "hdts", "wrs", "md",
    "3d",
    "encode", "hdrip", "bluray", "hevc", "fullhd",
]


def type_priority(tag: str) -> int:
    return TYPE_PRIORITY.index(tag) if tag in TYPE_PRIORITY else len(TYPE_PRIORITY)


# Year, season or resolution after the title
TITLE_END = re.compile(r"(?<![a-z0-9])(?:(?:19|20)\d{2}|s\d{1,2}(?:e\d+)?|\d{3,4}[pi])(?![a-z0-9])")

# NFRip, AMZNRip, DSNPRip..
PLATFORM_RIP = re.compile(
    r"(?<![a-z0-9])(?:" + "|".join(re.escape(tag.lower()) for tag, category in TAGS_LIST.items()
                                    if category == "platform") + r")rip(?![a-z0-9])")
