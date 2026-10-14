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
