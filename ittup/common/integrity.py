# -*- coding: utf-8 -*-
import json
import os
import re
import subprocess
from functools import cache

from ittup.common.utility import ManageTitles, System

# Where a few frames are decoded, in percent of the duration (CHECK_CORRUPTED_START/END): the frames at the end
# find the truncated files
DEFAULT_START = 10
DEFAULT_END = 90
SAMPLE_FRAMES = 3
FFPROBE_TIMEOUT = 120
# ffprobe 4.4 reads only the first of the -read_intervals: every file would look truncated
MIN_FFPROBE_VERSION = (5, 1)
# A truncated file has no frames this far before the end position: 5% of the duration, at least 10s because
# ffprobe seeks to the keyframe before each position
TRUNCATED_MARGIN = 0.05
TRUNCATED_MARGIN_SECONDS = 10

# ffmpeg logs a malformed Dolby Vision RPU as an error, drops that frame's metadata and still decodes the frame
DOLBY_VISION_ERROR = re.compile(r"\bRPU\b|DOVI|Dolby Vision", re.IGNORECASE)
# 'ffprobe version 4.4.2-0ubuntu0.22.04.1', 'ffprobe version n6.1.1'; the git builds ('N-112345-g...') have no number
FFPROBE_VERSION = re.compile(r"^ffprobe version n?(\d+)\.(\d+)")


class UnsupportedFFprobe(Exception):
    """
    The installed ffprobe is older than MIN_FFPROBE_VERSION
    """


class MediaIntegrity:
    """
    Find the corrupted video files with ffprobe before the upload
    """

    @staticmethod
    def video_files(path: str) -> list[str]:
        """
        The video file, or the video files of a folder
        """
        if not os.path.isdir(path):
            return [path]
        return [os.path.join(path, file) for file in sorted(os.listdir(path), key=System.natural_key)
                if ManageTitles.filter_ext(file)]

    @staticmethod
    def ffprobe(arguments: list[str]) -> tuple[int, str, str]:
        result = subprocess.run(["ffprobe", "-v", "error", *arguments], capture_output=True, text=True,
                                stdin=subprocess.DEVNULL, timeout=FFPROBE_TIMEOUT)
        return result.returncode, result.stdout, result.stderr.strip()

    @staticmethod
    @cache
    def ffprobe_version() -> tuple[str, tuple[int, int] | None]:
        """
        'ffprobe version ...' and its (major, minor), None if the version has no number
        """
        result = subprocess.run(["ffprobe", "-version"], capture_output=True, text=True,
                                stdin=subprocess.DEVNULL, timeout=FFPROBE_TIMEOUT)
        line = (result.stdout.splitlines() or [""])[0].split(" Copyright")[0].strip()
        match = FFPROBE_VERSION.match(line)
        return line, (int(match.group(1)), int(match.group(2))) if match else None

    @staticmethod
    def first_error(stderr: str, returncode: int) -> str:
        """
        First ffprobe error line without the '[matroska,webm @ 0x...]' prefix
        """
        if not stderr:
            return f"ffprobe exit code {returncode}"
        return re.sub(r"^\[[^]]*@ 0x[0-9a-f]+\]\s*", "", stderr.splitlines()[0])

    @staticmethod
    def sample_positions(start: int, end: int) -> tuple[float, float, float]:
        """
        Start, middle and end of the checked range, as fractions of the duration
        """
        return start / 100, (start + end) / 200, end / 100

    @staticmethod
    def split_dolby_vision(stderr: str) -> tuple[str, list[str]]:
        """
        The ffprobe errors without the Dolby Vision metadata ones, and the Dolby Vision ones
        """
        lines = stderr.splitlines()
        dolby_vision = [line for line in lines if DOLBY_VISION_ERROR.search(line)]
        return "\n".join(line for line in lines if line not in dolby_vision).strip(), dolby_vision

    @staticmethod
    def check_file(path: str, start: int = DEFAULT_START, end: int = DEFAULT_END,
                   ignore_dolby_vision: bool = False) -> tuple[str | None, str | None]:
        """
        Read the container and decode a few frames at the start, middle and end of the checked range

        :param start: start of the checked range, in percent of the duration
        :param end: end of the checked range, in percent of the duration
        :param ignore_dolby_vision: the Dolby Vision metadata errors don't make the file corrupted
        :return: (the error, None if the file is fine; the ignored Dolby Vision error, if any)
        """
        returncode, stdout, stderr = MediaIntegrity.ffprobe(
            ["-show_entries", "format=duration", "-of", "json", path])
        if returncode != 0:
            return MediaIntegrity.first_error(stderr, returncode), None
        try:
            duration = float(json.loads(stdout)["format"]["duration"])
        except (KeyError, ValueError, json.JSONDecodeError):
            return "unknown duration", None
        if duration <= 0:
            return "unknown duration", None

        intervals = ",".join(f"{duration * position:.2f}%+#{SAMPLE_FRAMES}"
                             for position in MediaIntegrity.sample_positions(start, end))
        returncode, stdout, stderr = MediaIntegrity.ffprobe(
            ["-select_streams", "v:0", "-read_intervals", intervals,
             "-show_entries", "frame=best_effort_timestamp_time", "-of", "csv=p=0", path])
        ignored = None
        if ignore_dolby_vision and returncode == 0:
            stderr, dolby_vision = MediaIntegrity.split_dolby_vision(stderr)
            if dolby_vision:
                ignored = MediaIntegrity.first_error(dolby_vision[0], returncode)
        if returncode != 0 or stderr:
            return MediaIntegrity.first_error(stderr, returncode), None

        timestamps = [float(line.strip(" ,")) for line in stdout.splitlines() if line.strip(" ,") not in ("", "N/A")]
        if not timestamps:
            return "no video frame decoded", None
        # The duration in the header is still the full one: a truncated file has no frames near the end
        if max(timestamps) < duration * end / 100 - max(duration * TRUNCATED_MARGIN, TRUNCATED_MARGIN_SECONDS):
            return f"truncated: no frames after {max(timestamps):.0f}s of {duration:.0f}s", None
        return None, ignored

    @staticmethod
    def check(path: str, start: int = DEFAULT_START, end: int = DEFAULT_END,
              ignore_dolby_vision: bool = False) -> tuple[dict[str, str], dict[str, str]]:
        """
        Check the file or every video file of a folder

        :return: ({file: error} for the corrupted files, empty if they are all fine;
                  {file: Dolby Vision error} for the fine files with ignored Dolby Vision errors)
        :raises FileNotFoundError: ffprobe is not installed
        :raises UnsupportedFFprobe: ffprobe is older than MIN_FFPROBE_VERSION
        """
        line, version = MediaIntegrity.ffprobe_version()
        if version is not None and version < MIN_FFPROBE_VERSION:
            raise UnsupportedFFprobe(line)
        errors, ignored = {}, {}
        for file in MediaIntegrity.video_files(path):
            try:
                error, dolby_vision = MediaIntegrity.check_file(file, start, end, ignore_dolby_vision)
            except subprocess.TimeoutExpired:
                error, dolby_vision = f"ffprobe timeout ({FFPROBE_TIMEOUT}s)", None
            if error:
                errors[file] = error
            elif dolby_vision:
                ignored[file] = dolby_vision
        return errors, ignored
