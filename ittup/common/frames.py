# -*- coding: utf-8 -*-
import os
import json
import subprocess
import io

from concurrent.futures import ThreadPoolExecutor
from functools import cache
from pathlib import Path
from PIL import Image, ImageStat

from ittup.common import config_settings
from ittup.view import custom_console

# Transfer characteristics of the HDR videos: PQ (HDR10, HDR10+, Dolby Vision with HDR10 base layer) and HLG
HDR_TRANSFERS = ('smpte2084', 'arib-std-b67')

# HDR -> SDR: linear light, BT.709 primaries, Hable tone mapping, back to BT.709 8 bit
TONEMAP_FILTER = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
                  "tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")

# HDR/Dolby Vision -> SDR on the GPU (Vulkan). libplacebo applies the Dolby Vision RPU reshaping, needed by
# profile 5 (IPTPQc2, no HDR10 base layer): without it the colors are green and purple
LIBPLACEBO_FILTER = ("libplacebo=tonemapping=auto:colorspace=bt709:color_primaries=bt709:color_trc=bt709:"
                     "range=tv:format=yuv420p")

# A frame with a mean luminance (0-255) below this value is considered too dark for a screenshot
DARK_FRAME_THRESHOLD = 40

# How many other positions to try around a dark frame before keeping the brightest one
DARK_FRAME_RETRIES = 4

# Screenshots extracted at the same time (ffmpeg processes)
EXTRACT_WORKERS = 4


@cache
def ffmpeg_can_tonemap() -> bool:
    """
    The tone mapping needs an ffmpeg build with the 'zscale' (libzimg) and 'tonemap' filters
    """
    try:
        result = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True, check=True,
                                stdin=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    filters = {line.split()[1] for line in result.stdout.splitlines() if len(line.split()) > 2}
    return {'zscale', 'tonemap'} <= filters


@cache
def ffmpeg_can_libplacebo() -> bool:
    """
    The 'libplacebo' filter needs an ffmpeg build with libplacebo and a working Vulkan device:
    try it on a test frame
    """
    command = ["ffmpeg", "-hide_banner", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=64x64:d=0.1",
               "-vf", LIBPLACEBO_FILTER, "-frames:v", "1", "-f", "null", "-"]
    try:
        subprocess.run(command, capture_output=True, stdin=subprocess.DEVNULL, check=True, timeout=30)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False
    return True


class VideoFrame:
    def __init__(self, video_path: str, num_screenshots: int):
        """
        Initialize VideoFrame object

        :param video_path: Path to the video file
        :param num_screenshots: Number of screenshots to take
        """
        self.video_path = Path(video_path)
        # Number of screenshots based on the user's preferences
        self.num_screenshots = num_screenshots
        # ffmpeg '-vf' option for the screenshots, set by create()
        self.video_filter: list[str] = []

    def create(self):
        """
        Create screenshots from the video

        :return: A list of screenshots in bytes and a flag indicating if any screenshot is HD
        """
        self.video_filter = self._get_video_filter()
        frames = self._extract()
        frames_in_bytes = []
        is_hd = 0

        for idx, frame in enumerate(frames):
            img_bytes = self.image_to_bytes(frame=frame)
            is_hd = 0 if frame.height >= 720 else 1
            frames_in_bytes.append(img_bytes)

        return frames_in_bytes, is_hd

    def image_to_bytes(self, frame: Image) -> bytes:
        """
        Convert an image to bytes

        :param frame: The image to convert
        :return: Image in bytes
        :compress_level: compressione level (0-9); 9=Max; default=4 ; 0 = best
        """
        image = self.resize_image(frame)
        buffered = io.BytesIO()
        user_compress_level: int = config_settings.user_preferences.COMPRESS_SCSHOT\
            if 0 <= config_settings.user_preferences.COMPRESS_SCSHOT <= 9 else 4
        image.save(
            buffered, format="PNG", optimize=True, compress_level=user_compress_level
        )
        return buffered.getvalue()

    @staticmethod
    def resize_image(image: Image, width: int = 650) -> Image:
        """
        Resize the image while maintaining aspect ratio

        :param image: The image to resize
        :param width: The width to resize to
        :return: Resized image
        """
        if config_settings.user_preferences.RESIZE_SCSHOT:
            aspect_ratio = image.width / image.height
            height = round(width / aspect_ratio)
            resized_image = image.resize((width, height), Image.Resampling.LANCZOS)
            return resized_image
        else:
            return image

    def _extract(self):
        """
        Extract frames from the video based on the number of screenshots

        :return: A list of frames
        """
        duration = self._get_video_duration()
        min_time = duration * 0.10
        max_time = duration * 0.90
        interval = int(max_time - min_time)
        duration_step = interval // self.num_screenshots
        min_time = int(min_time)
        max_time = int(max_time)
        times = list(range(min_time + duration_step, max_time, duration_step))
        if len(times) < self.num_screenshots:
            times.append(max_time)

        # One ffmpeg process for each screenshot, at the same time
        with ThreadPoolExecutor(max_workers=EXTRACT_WORKERS) as executor:
            return list(executor.map(lambda time_: self._extract_bright_frame(time_, duration_step, duration), times))

    def _extract_bright_frame(self, time_: int, duration_step: int, duration: float) -> Image:
        """
        Extract the frame at 'time_'. If it is too dark try a few positions around it, within the same
        interval between two screenshots, and keep the first bright one or the brightest one

        :param time_: The time of the screenshot
        :param duration_step: The distance between two screenshots
        :param duration: Duration of the video in seconds
        :return: The extracted frame as a PIL Image
        """
        frame = self._extract_frame(time_)
        brightness = self.brightness(frame)
        if brightness >= DARK_FRAME_THRESHOLD:
            return frame

        # +offset, -offset, +2*offset, -2*offset ...
        offset = max(1, duration_step // (DARK_FRAME_RETRIES + 2))
        for attempt in range(1, DARK_FRAME_RETRIES + 1):
            shift = offset * ((attempt + 1) // 2) * (1 if attempt % 2 else -1)
            candidate_time = time_ + shift
            if not 0 <= candidate_time < duration:
                continue
            candidate = self._extract_frame(candidate_time)
            candidate_brightness = self.brightness(candidate)
            if candidate_brightness > brightness:
                frame, brightness = candidate, candidate_brightness
            if brightness >= DARK_FRAME_THRESHOLD:
                break
        return frame

    @staticmethod
    def brightness(frame: Image) -> float:
        """
        Mean luminance of the frame (0-255)
        """
        return ImageStat.Stat(frame.convert("L")).mean[0]

    def _get_video_filter(self) -> list[str]:
        """
        ffmpeg options for the screenshots: HDR videos are tone mapped to SDR, otherwise the colors look washed out.
        Dolby Vision profile 5 has no HDR transfer (it is 'unknown') and without the RPU reshaping the colors
        are green and purple: only libplacebo can fix it

        :return: The '-vf' option or an empty list
        """
        command = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=color_transfer:stream_side_data=dv_profile",
            "-of",
            "json",
            str(self.video_path),
        ]
        try:
            result = subprocess.run(command, capture_output=True, stdin=subprocess.DEVNULL, text=True, check=True)
            streams = json.loads(result.stdout).get("streams", [])
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            # ffprobe errors are reported by _get_video_duration()
            return []

        stream = streams[0] if streams else {}
        color_transfer = stream.get("color_transfer", "")
        dv_profile = next((side_data["dv_profile"] for side_data in stream.get("side_data_list", [])
                           if "dv_profile" in side_data), None)
        if color_transfer not in HDR_TRANSFERS and dv_profile is None:
            return []

        hdr_format = f"Dolby Vision profile {dv_profile}" if dv_profile is not None else color_transfer
        if ffmpeg_can_libplacebo():
            custom_console.bot_log(f"HDR video ({hdr_format}): tone mapping the screenshots to SDR with libplacebo")
            return ["-vf", LIBPLACEBO_FILTER]

        if color_transfer not in HDR_TRANSFERS:
            custom_console.bot_warning_log(f"HDR video ({hdr_format}): ffmpeg without a working 'libplacebo' filter"
                                           " (Vulkan), the screenshots have wrong colors")
            return []

        if not ffmpeg_can_tonemap():
            custom_console.bot_warning_log("HDR video: ffmpeg without the 'zscale' filter (libzimg),"
                                           " the screenshots are not tone mapped")
            return []

        custom_console.bot_log(f"HDR video ({hdr_format}): tone mapping the screenshots to SDR")
        return ["-vf", TONEMAP_FILTER]

    def _get_video_duration(self) -> float:
        """
        Get the duration of the video

        :return: Duration of the video in seconds
        :raises RuntimeError: If ffprobe fails
        """
        command = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(self.video_path),
        ]
        try:
            result = subprocess.run(command, capture_output=True, stdin=subprocess.DEVNULL, text=True, check=True)
            duration = float(result.stdout.strip())
        except subprocess.CalledProcessError:
            custom_console.bot_error_log(
                f"ffprobe error: The media is invalid {self.video_path}"
            )
            exit(1)
        except FileNotFoundError:
            custom_console.bot_error_log(
                "[FFMPEG-ffprobe not found] - Install ffmpeg or check your system path"
            )
            exit(1)
        return duration

    def _extract_frame(self, time_: float) -> Image:
        """
        Extract a single frame from the video at the specified time

        :param time: The time to extract the frame
        :return: The extracted frame as a PIL Image
        :raises RuntimeError: If it fails
        """
        command = [
            "ffmpeg",
            "-ss",
            str(time_),
            "-i",
            str(self.video_path),
            *self.video_filter,
            "-vframes",
            "1",
            "-threads",
            "4",
            "-f",
            "image2pipe",
            "-",
        ]
        try:
            # No stdin: the ffmpeg processes running at the same time would change the terminal settings
            # and leave it without echo and Enter, so the questions to the user could not be answered
            result = subprocess.run(command, capture_output=True, stdin=subprocess.DEVNULL, check=True, timeout=20)
            return Image.open(io.BytesIO(result.stdout))
        except subprocess.CalledProcessError as e:
            custom_console.bot_error_log(f"IMAGES Error: Please verify if your file is corrupted")
            exit(1)
        except subprocess.TimeoutExpired:
            custom_console.bot_error_log(f"IMAGES Error: Time Out. Please verify if your file is corrupted")
            exit(1)
        except FileNotFoundError:
            custom_console.bot_error_log(
                "[FFMPEG not found] - Install ffmpeg or check your system path")
            exit(1)
        except Image.UnidentifiedImageError as e:
            custom_console.bot_error_log(f"IMAGES Error: {self.video_path}  Cannot identify image file. "
                                         f"Please verify if your file is corrupted")
            exit(1)

    @staticmethod
    def create_webp_from_video(video_path, start_time, duration, output_path):
        """
        Create a webp file

        :param duration: how many sec
        :param video_path: The path of the video
        :start_time: The start time of the video
        :video_height: The height of the video
        :param output_path: The path of the output webp file

        :return: The extracted frame as a PIL Image

        raises RuntimeError: If it fails
        remove hostimage from the unit3d whitelist:
        https://wsrv.nl/ 71kk pixel limit and 10sec timeout processing for the whitelisted in Unit3d
        note for the webp file: https://github.com/weserv/images/wiki/Animated-.gif-and-file-extensions
        """
        command = [
            "ffmpeg",
            "-y",
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", video_path,
            "-vf", f"fps=7",
            "-c:v", "libwebp",
            "-quality", "50",
            "-loop", "0", # infinite
            "-f", "webp",
            output_path
        ]

        try:
            subprocess.run(command, capture_output=True, stdin=subprocess.DEVNULL, check=True)
            if not os.path.isfile(output_path):
                print(f"file {output_path} doesn't exist !")
                exit(1)
            webp_file = open(output_path, "rb")
            webp_file_content = webp_file.read()
            webp_file.close()
            os.remove(output_path)
            custom_console.bot_log(f"webp file {output_path} created")
            return [webp_file_content]

        except subprocess.CalledProcessError as e:
            custom_console.bot_error_log(f"IMAGES Error: Please verify if your file is corrupted {e}")
        except FileNotFoundError:
            custom_console.bot_error_log(
                "[FFMPEG not found] - Install ffmpeg or check your system path")
            exit(1)
        except Image.UnidentifiedImageError as e:
            custom_console.bot_error_log(f"IMAGES Error: {output_path}  Cannot identify image file. "
                                         f"Please verify if your file is corrupted")

        return None

