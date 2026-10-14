# -*- coding: utf-8 -*-
import os
import re

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


def rename_to_title(path: str, display_name: str, video_files: list[str], pack: str | None,
                    episodes: dict[str, tuple[int | None, int | None]]) -> tuple[str, dict[str, str]]:
    """
    Rename a file, or a folder and its video files, as the title shown on the tracker

    Args:
        path: the file or the folder of the torrent
        display_name: the title shown on the tracker
        video_files: the video files in the folder (names)
        pack: the season tag of the title (es. 'S04') for a tv pack
        episodes: (season, episode) of each video file of a pack

    Returns:
        the new path and the new name of each renamed file of the folder
    """
    name = title_name(display_name)
    if os.path.isfile(path):
        _, ext = os.path.splitext(path)
        return rename_path(path, name + ext), {}

    renamed = {}
    for file in video_files:
        _, ext = os.path.splitext(file)
        if pack:
            new_name = episode_name(name, pack, *episodes.get(file, (None, None)))
        else:
            # A movie folder: only its single video file takes the title
            new_name = name if len(video_files) == 1 else None
        if not new_name:
            continue
        new_path = rename_path(os.path.join(path, file), new_name + ext)
        if new_path != os.path.join(path, file):
            renamed[file] = os.path.basename(new_path)
    return rename_path(path, name), renamed
