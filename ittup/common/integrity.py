# -*- coding: utf-8 -*-
import json
import os
import re
import subprocess

from ittup.common.utility import ManageTitles, System

# Where a few frames are decoded, as a fraction of the duration: the last one finds the truncated files
SAMPLE_POSITIONS = (0.10, 0.50, 0.95)
SAMPLE_FRAMES = 3
FFPROBE_TIMEOUT = 120


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
    def first_error(stderr: str, returncode: int) -> str:
        """
        First ffprobe error line without the '[matroska,webm @ 0x...]' prefix
        """
        if not stderr:
            return f"ffprobe exit code {returncode}"
        return re.sub(r"^\[[^]]*@ 0x[0-9a-f]+\]\s*", "", stderr.splitlines()[0])

    @staticmethod
    def check_file(path: str) -> str | None:
        """
        Read the container and decode a few frames at the start, middle and end of the video

        :return: the error, None if the file is fine
        """
        returncode, stdout, stderr = MediaIntegrity.ffprobe(
            ["-show_entries", "format=duration", "-of", "json", path])
        if returncode != 0:
            return MediaIntegrity.first_error(stderr, returncode)
        try:
            duration = float(json.loads(stdout)["format"]["duration"])
        except (KeyError, ValueError, json.JSONDecodeError):
            return "unknown duration"
        if duration <= 0:
            return "unknown duration"

        intervals = ",".join(f"{duration * position:.2f}%+#{SAMPLE_FRAMES}" for position in SAMPLE_POSITIONS)
        returncode, stdout, stderr = MediaIntegrity.ffprobe(
            ["-select_streams", "v:0", "-read_intervals", intervals,
             "-show_entries", "frame=best_effort_timestamp_time", "-of", "csv=p=0", path])
        if returncode != 0 or stderr:
            return MediaIntegrity.first_error(stderr, returncode)

        timestamps = [float(line.strip(" ,")) for line in stdout.splitlines() if line.strip(" ,") not in ("", "N/A")]
        if not timestamps:
            return "no video frame decoded"
        # The duration in the header is still the full one: a truncated file has no frames near the end
        if max(timestamps) < duration * 0.90:
            return f"truncated: no frames after {max(timestamps):.0f}s of {duration:.0f}s"
        return None

    @staticmethod
    def check(path: str) -> dict[str, str]:
        """
        Check the file or every video file of a folder

        :return: {file: error} for the corrupted files, empty if they are all fine
        :raises FileNotFoundError: ffprobe is not installed
        """
        errors = {}
        for file in MediaIntegrity.video_files(path):
            try:
                error = MediaIntegrity.check_file(file)
            except subprocess.TimeoutExpired:
                error = f"ffprobe timeout ({FFPROBE_TIMEOUT}s)"
            if error:
                errors[file] = error
        return errors
