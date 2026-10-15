# -*- coding: utf-8 -*-
import os
import re
from dataclasses import dataclass

import guessit

from ittup.common.trackers.tags_list import TAGS_LIST
from ittup.view import custom_console

# Characters the tracker (UNIT3D) doesn't accept in the names of the torrent files
INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def safe_name(name: str) -> str:
    """
    Name without the characters refused by the tracker: 'Titolo: Sub' -> 'Titolo - Sub'
    The extension is kept, the trailing dots and spaces are removed
    """
    stem, ext = os.path.splitext(name)
    # Keep only a real extension (es. '.mkv'), not the end of 'Mr. Robot'
    if not re.fullmatch(r"\.[A-Za-z0-9]{1,5}", ext):
        stem, ext = name, ""
    if " " in stem:
        stem = re.sub(r"\s*:\s*", " - ", stem)
    else:
        stem = stem.replace(":", ".")
    stem = INVALID_CHARS.sub("", stem)
    stem = re.sub(r"\s{2,}", " ", stem)
    stem = re.sub(r"\.{2,}", ".", stem)
    stem = re.sub(r"(\s-)+\s", " - ", stem)
    return stem.strip(" .") + ext


def is_valid_name(name: str) -> bool:
    return not INVALID_CHARS.search(name) and name == name.rstrip(" .")


def rename_path(path: str, new_name: str) -> str:
    """
    Rename a file or a folder in the same folder. Returns the new path, the old one if it can't be renamed
    """
    new_path = os.path.join(os.path.dirname(path), new_name)
    if new_path == path:
        return path
    if os.path.exists(new_path):
        custom_console.bot_error_log(f"Can't rename '{path}': '{new_name}' already exists")
        return path
    try:
        os.rename(path, new_path)
    except OSError as e:
        custom_console.bot_error_log(f"Can't rename '{path}': {e}")
        return path
    custom_console.bot_warning_log(f"Renamed '{os.path.basename(path)}' -> '{new_name}'")
    return new_path


def rename_invalid(path: str) -> str:
    """
    Rename the file, or the folder and everything in it, whose names have characters refused by the tracker
    Returns the new path
    """
    path = os.path.normpath(path)
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files + dirs:
                if not is_valid_name(name):
                    rename_path(os.path.join(root, name), safe_name(name))
    name = os.path.basename(path)
    if is_valid_name(name):
        return path
    return rename_path(path, safe_name(name))


def title_name(display_name: str) -> str:
    """
    File name from the title shown on the tracker, with dots:
    'Spider-Man: No Way Home 2021 1080p WEB-DL H.264-SIGN' -> 'Spider-Man.No.Way.Home.2021.1080p.WEB-DL.H.264-SIGN'
    """
    name = INVALID_CHARS.sub(" ", display_name)
    name = re.sub(r"\s+-\s+", ".", name.strip())
    name = re.sub(r"\s+", ".", name)
    name = re.sub(r"\.{2,}", ".", name)
    return name.strip(".")


def episode_name(name: str, pack: str | None, season: int | None, episode: int | None) -> str | None:
    """
    Name of an episode of a pack: the pack tag of the title is replaced by its SxxExx
    None if the episode or the pack tag are unknown
    """
    if not pack or season is None or episode is None:
        return None
    pattern = rf"(?<![^.]){re.escape(pack)}(?![^.])"
    if not re.search(pattern, name):
        return None
    return re.sub(pattern, f"S{int(season):02d}E{int(episode):02d}", name, count=1)


@dataclass
class TitleInfo:
    """
    What the name of a file should say, from the title shown on the tracker and MediaInfo
    """
    resolution: str | None = None
    # Video codec family from MediaInfo: '264' or '265'
    family: str | None = None
    # Source and remux tags of the title (es. 'WEB-DL', 'BluRay REMUX')
    source: str | None = None
    year: int | None = None


@dataclass
class RenamePlan:
    # None: the name is kept
    new_name: str | None
    reason: str


# Resolution, year and source in a release name
RESOLUTION = re.compile(r"(?<![^\W_])\d{3,4}[pi](?![^\W_])", re.IGNORECASE)
YEAR = re.compile(r"(?<![^\W_])(?:19|20)\d{2}(?![^\W_])")
SOURCE = re.compile(r"(?<![^\W_])(?:" + "|".join(
    re.escape(tag) for tag, category in sorted(TAGS_LIST.items(), key=lambda item: -len(item[0]))
    if category in ("source", "remux")) + r")(?![^\W_])", re.IGNORECASE)
# x264, H.265, AVC, HEVC..
VIDEO_CODEC = re.compile(r"(?<![a-z0-9])(?:[xh][._ -]?26([45])|(avc)|(hevc))(?![a-z0-9])", re.IGNORECASE)


def codec_family(name: str) -> str | None:
    """
    Video codec family written in a name: '264', '265', None if missing or ambiguous
    """
    families = {f"26{m.group(1)}" if m.group(1) else "264" if m.group(2) else "265" for m in VIDEO_CODEC.finditer(name)}
    return families.pop() if len(families) == 1 else None


def plan_name(name: str, target: str, info: TitleInfo | None) -> RenamePlan:
    """
    Check the name of a file (without extension) against what it should say before renaming it as the title:
    - a name with only the title (and the year or the season) is renamed as the title
    - a name whose resolution, year or video codec don't match MediaInfo, or that misses the resolution,
      the video codec or the audio codec, is renamed as the title
    - a name with everything but the source gets the source of the title (read from MediaInfo when the name had
      none), in its own style
    - otherwise the name is kept

    Args:
        name: the current name
        target: the name from the title shown on the tracker
        info: what the name should say
    """
    info = info or TitleInfo()
    guess = guessit.guessit(name)
    has_source = bool(SOURCE.search(name) or guess.get("source"))
    name_family = codec_family(name)
    has_video = bool(name_family or guess.get("video_codec"))
    has_audio = bool(guess.get("audio_codec"))
    resolution = RESOLUTION.search(name)

    if name == target:
        return RenamePlan(None, "it is already the title")
    if not (resolution or has_source or has_video or has_audio):
        return RenamePlan(target, "the name has only the title")

    if resolution and info.resolution and resolution.group(0).lower() != info.resolution.lower():
        return RenamePlan(target, f"the name says {resolution.group(0)}, MediaInfo {info.resolution}")
    if name_family and info.family and name_family != info.family:
        return RenamePlan(target, f"the name says the codec {name_family}, MediaInfo {info.family}")
    year = guess.get("year")
    if isinstance(year, int) and info.year and year != int(info.year):
        return RenamePlan(target, f"the name says the year {year}, the title {info.year}")

    missing = [label for label, found in (("resolution", resolution), ("video codec", has_video),
                                          ("audio codec", has_audio)) if not found]
    if missing:
        return RenamePlan(target, f"the name misses: {', '.join(missing)}")

    if has_source:
        return RenamePlan(None, "the name already has every information")
    if not info.source:
        return RenamePlan(None, "the name has every information but the source, unknown in MediaInfo too")
    return RenamePlan(add_source(name, info.source, after=resolution),
                      f"added the source '{info.source}' missing from the name")


def add_source(name: str, source: str, after: re.Match) -> str:
    """
    Write the source after the resolution, with the separator of the name: 'Movie.2020.1080p.H.264' -> '..1080p.WEB-DL.H.264'
    """
    separator = " " if " " in name else "." if "." in name else "_" if "_" in name else " "
    return name[:after.end()] + separator + separator.join(source.split()) + name[after.end():]


def apply_plan(path: str, plan: RenamePlan, ext: str = "") -> str:
    """
    Rename the file as planned and log why. Returns the new path
    """
    name = os.path.basename(path)
    if not plan.new_name:
        custom_console.bot_log(f"[RENAME_FILES] '{name}' kept: {plan.reason}")
        return path
    custom_console.bot_log(f"[RENAME_FILES] '{name}': {plan.reason}")
    return rename_path(path, plan.new_name + ext)


def rename_to_title(path: str, display_name: str, video_files: list[str], pack: str | None,
                    episodes: dict[str, tuple[int | None, int | None]],
                    info: TitleInfo | None = None) -> tuple[str, dict[str, str]]:
    """
    Rename a file, or a folder and its video files, as the title shown on the tracker
    Each name is checked first (plan_name): a complete name is kept, or only gets the missing source

    Args:
        path: the file or the folder of the torrent
        display_name: the title shown on the tracker
        video_files: the video files in the folder (names)
        pack: the season tag of the title (es. 'S04') for a tv pack
        episodes: (season, episode) of each video file of a pack
        info: what the names should say (resolution, codec, source.. from MediaInfo)

    Returns:
        the new path and the new name of each renamed file of the folder
    """
    name = title_name(display_name)
    custom_console.bot_log(f"[RENAME_FILES] Checking the names of '{os.path.basename(path)}'"
                           f" against the title '{name}'")
    if os.path.isfile(path):
        stem, ext = os.path.splitext(os.path.basename(path))
        return apply_plan(path, plan_name(stem, name, info), ext), {}

    renamed = {}
    for file in video_files:
        stem, ext = os.path.splitext(file)
        if pack:
            target = episode_name(name, pack, *episodes.get(file, (None, None)))
        else:
            # A movie folder: only its single video file takes the title
            target = name if len(video_files) == 1 else None
        if not target:
            continue
        file_path = os.path.join(path, file)
        new_path = apply_plan(file_path, plan_name(stem, target, info), ext)
        if new_path != file_path:
            renamed[file] = os.path.basename(new_path)
    return apply_plan(path, plan_name(os.path.basename(path), name, info)), renamed
