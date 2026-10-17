# -*- coding: utf-8 -*-

import base64
import json
import time
import requests

from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from ittup.common import config_settings
from ittup.view import custom_console


# Screenshots uploaded at the same time
UPLOAD_WORKERS = 4

# Attempts to upload a screenshot to a host before trying the next one
UPLOAD_ATTEMPTS = 4

# Seconds to connect, and to wait for the answer: a full resolution PNG takes the host a while to process,
# more so with more screenshots uploaded at the same time
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 120

# HTTP errors worth another attempt: the others (e.g. 400 image too big) fail again with the same screenshot
RETRY_HTTP_STATUS = (408, 429)


class ImageUploader(ABC):
    def __init__(self, image: bytes, key: str, image_name: str):
        self.image = base64.b64encode(image)
        self.key = key
        self.image_name = image_name
        self.timeout = (CONNECT_TIMEOUT, READ_TIMEOUT)

    @abstractmethod
    def get_endpoint(self):
        pass

    @abstractmethod
    def get_data(self):
        pass

    @abstractmethod
    def get_field_name(self):
        pass

    def upload(self):
        data = self.get_data()
        files = {
            self.get_field_name(): (None, self.image),
        }

        upload_n = 0
        while upload_n < UPLOAD_ATTEMPTS:
            try:
                upload_n += 1
                response = requests.post(
                    self.get_endpoint(), data = data, files = files, timeout = self.timeout
                )
                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                self.handle_http_error(e, upload_n)
                if e.response is None or (e.response.status_code < 500
                                          and e.response.status_code not in RETRY_HTTP_STATUS):
                    break

            # A timeout, a dropped connection or a broken answer is often temporary (e.g. more screenshots
            # uploaded at the same time): try again instead of losing the screenshot
            except json.decoder.JSONDecodeError as e:
                # or Maintenance mode
                custom_console.bot_log(f"[{self.__class__.__name__} try n° {upload_n}] JSONDecodeError"
                       f" Connection issue. Please check your connection or the website")

            except requests.exceptions.Timeout:
                custom_console.bot_log(
                    f"[{self.__class__.__name__} try n° {upload_n}] We did not receive a response from the server"
                    f" within the {READ_TIMEOUT} second limit"
                )

            except requests.exceptions.RequestException as e:
                custom_console.bot_log(f"[{self.__class__.__name__} try n° {upload_n}] Connection error: {e}")

            if upload_n < UPLOAD_ATTEMPTS:
                time.sleep(upload_n)

        return None

    def handle_http_error(self, error, attempt):
        try:
            message = json.loads(error.response.content.decode("utf8"))
            if message.get("status_code") == 400:
                custom_console.bot_error_log(
                    f"[Error {self.__class__.__name__}] '{message['error']['message']}'"
                )
            else:
                custom_console.bot_error_log(
                    f"[Report {self.__class__.__name__} try n° {attempt}]-> {message['error']['message']}"
                )

        # Not a JSON answer, or not the usual {'error': {'message': ...}}
        except (json.decoder.JSONDecodeError, AttributeError, KeyError, TypeError):
            custom_console.bot_error_log(f"HTTPError received: {error}")


class ImgBB(ImageUploader):

    priority= config_settings.user_preferences.IMGBB_PRIORITY
    def get_endpoint(self) -> str:
        return "https://api.imgbb.com/1/upload"

    def get_data(self) -> dict:
        return {
            "key": self.key,
            "name": self.image_name,
        }

    def get_field_name(self) -> str:
        return 'image'


class Freeimage(ImageUploader):

    priority = config_settings.user_preferences.FREE_IMAGE_PRIORITY
    def get_endpoint(self) -> str:
        return "https://freeimage.host/api/1/upload"

    def get_data(self) -> dict:
        return {
            "key": self.key,
            "format": "json",
            "name": self.image_name,
        }

    def get_field_name(self) -> str:
        return 'image'


class PtScreens(ImageUploader):

    priority= config_settings.user_preferences.PTSCREENS_PRIORITY
    def get_endpoint(self) -> str:
        return "https://ptscreens.com/api/1/upload"

    def get_data(self) -> dict:
        return {
            "key": self.key,
            "title": self.image_name,
        }

    def get_field_name(self) -> str:
        return 'source'


class LensDump(ImageUploader):

    priority= config_settings.user_preferences.LENSDUMP_PRIORITY
    def get_endpoint(self) -> str:
        return "https://lensdump.com/api/1/upload"

    def get_data(self) -> dict:
        return {
            "key": self.key,
            "title": self.image_name,
        }

    def get_field_name(self) -> str:
        return 'source'


class ImgFi(ImageUploader):

    priority= config_settings.user_preferences.IMGFI_PRIORITY
    def get_endpoint(self) -> str:
        return "https://imgfi.com/api/1/upload"

    def get_data(self) -> dict:
        return {
            "key": self.key,
            "title": self.image_name,
        }

    def get_field_name(self) -> str:
        return 'source'

class PassIMA(ImageUploader):

    priority= config_settings.user_preferences.PASSIMA_PRIORITY
    def get_endpoint(self) -> str:
        return "https://passtheima.ge/api/1/upload"

    def get_data(self) -> dict:
        return {
            "key": self.key,
            "title": self.image_name,
        }

    def get_field_name(self) -> str:
        return 'source'


class ImaRide(ImageUploader):

    priority= config_settings.user_preferences.IMARIDE_PRIORITY
    def get_endpoint(self) -> str:
        return "https://www.imageride.net/api/1/upload"

    def get_data(self) -> dict:
        return {
            "key": self.key,
            "title": self.image_name,
        }

    def get_field_name(self) -> str:
        return 'source'

class ImageUploaderFallback:
    def __init__(self, uploader):
        self.uploader = uploader

    def upload(self, test=False) -> str:
        result = None

        # Get response from the uploader
        response = self.uploader.upload()

        # If not None get a new url
        if response:
            try:
                result = ImageUploaderFallback.result(
                    response=response, uploader_host=self.uploader.__class__.__name__
                )
            # An answer without the URL: this host failed, the next one may not
            except (KeyError, TypeError):
                custom_console.bot_error_log(
                    f"[{self.uploader.__class__.__name__}] Unexpected answer, no image URL"
                )

        # If there is no error from json response
        if result:
            """
            custom_console.bot_log(f"[{self.uploader.__class__.__name__}]..... [ON-LINE]")
            """
            if not test:
                return result

        # send an off-line message
        if not result:
            custom_console.bot_log(
                f"[{self.uploader.__class__.__name__}]..... [OFF-LINE]"
            )
        return result

    @staticmethod
    def result(response: dict, uploader_host: str) -> str | None:

        if uploader_host == "Freeimage":
            return response["image"]["image"]["url"]

        if uploader_host == "ImgBB":
            return response["data"]["image"]["url"]

        if uploader_host == "LensDump":
            return response['image']['url']

        if uploader_host == "PtScreens":
            return response['image']['url']

        if uploader_host == "ImgFi":
            return response['image']['url']

        if uploader_host == "PassIMA":
            return response['image']['url']

        if uploader_host == "ImaRide":
            return response['image']['url']

        return None

class Build:
    """
    - Upload screenshots and create a new description
    """

    def __init__(self, extracted_frames: list[bytes], filename: str):

        # Image filename
        self.filename = filename

        # Hosts that failed a screenshot of this description: the next screenshots try the other hosts first.
        # Not shared with the other uploads, a host that failed once would be skipped until ittup is restarted
        self.offline_uploaders: list[str] = []

        # Host APi keys
        self.IMGBB_KEY = config_settings.tracker_config.IMGBB_KEY
        self.FREE_IMAGE_KEY = config_settings.tracker_config.FREE_IMAGE_KEY
        self.LENSDUMP_KEY= config_settings.tracker_config.LENSDUMP_KEY
        self.PTSCREENS_KEY= config_settings.tracker_config.PTSCREENS_KEY
        self.IMGFI_KEY = config_settings.tracker_config.IMGFI_KEY
        self.PASSIMA_KEY = config_settings.tracker_config.PASSIMA_KEY
        self.IMARIDE_KEY = config_settings.tracker_config.IMARIDE_KEY
        self.extracted_frames = extracted_frames

    @staticmethod
    def has_key(key: str | None) -> bool:
        # A host without an API key in settings.json ('no_key' or empty) can't upload
        return bool(key and key.strip()) and 'no_key' not in key.lower()

    def upload_image(self, number: int, img_bytes: bytes) -> str | None:
        """
        Upload a screenshot to the first on-line host, in order of priority

        :return: the image URL, None if every host failed
        """
        image_name = f"{self.filename}.id_{number}"

        hosts = [
            (ImgBB, self.IMGBB_KEY),
            (Freeimage, self.FREE_IMAGE_KEY),
            (PtScreens, self.PTSCREENS_KEY),
            (LensDump, self.LENSDUMP_KEY),
            (ImgFi, self.IMGFI_KEY),
            (PassIMA, self.PASSIMA_KEY),
            (ImaRide, self.IMARIDE_KEY),
        ]

        # Skip the hosts without an API key, before the uploader encodes its own copy of the screenshot
        master_uploaders = [host(img_bytes, key, image_name=image_name) for host, key in hosts if self.has_key(key)]

        # Sorting list based on priority
        master_uploaders.sort(key=lambda uploader: uploader.priority)

        # The off-line hosts last: a temporary error on another screenshot doesn't mean this one fails too,
        # skipping them could lose the screenshot (e.g. a single host)
        online_uploaders = [uploader for uploader in master_uploaders
                            if uploader.__class__.__name__ not in self.offline_uploaders]
        offline_uploaders = [uploader for uploader in master_uploaders if uploader not in online_uploaders]

        for uploader in online_uploaders + offline_uploaders:
            # Upload the screenshot
            fallback_uploader = ImageUploaderFallback(uploader)
            # Get a new URL
            img_url = fallback_uploader.upload()

            # If it goes offline during upload skip the uploader
            if not img_url:
                custom_console.bot_error_log(
                    "** Upload failed, skip to next host **"
                )
                # Other screenshots may have found it offline at the same time
                if uploader.__class__.__name__ not in self.offline_uploaders:
                    self.offline_uploaders.append(uploader.__class__.__name__)
                continue
            custom_console.bot_log(img_url)
            return img_url

        custom_console.bot_error_log(f"Screenshot n° {number} not uploaded: every image host failed")
        return None

    def safe_upload_image(self, number: int, img_bytes: bytes) -> str | None:
        """
        upload_image() that loses only this screenshot on an unexpected error, not the whole description
        """
        try:
            return self.upload_image(number, img_bytes)
        except Exception as e:
            custom_console.bot_error_log(f"Screenshot n° {number} not uploaded: {e!r}")
            return None

    def description(self) -> str:
        description = "[center]\n"

        custom_console.bot_log(f"\n[STARTING IMAGE UPLOAD..]")
        keys = [self.IMGBB_KEY, self.FREE_IMAGE_KEY, self.LENSDUMP_KEY, self.PTSCREENS_KEY, self.IMGFI_KEY,
                self.PASSIMA_KEY, self.IMARIDE_KEY]
        if not any(self.has_key(key) for key in keys):
            custom_console.bot_error_log("No image host API key found in settings.json, skip the upload")
            return description + "\n[/center]"

        # Upload the screenshots at the same time, the description keeps their order
        with ThreadPoolExecutor(max_workers=UPLOAD_WORKERS) as executor:
            urls = list(executor.map(self.safe_upload_image, range(1, len(self.extracted_frames) + 1),
                                     self.extracted_frames))

        for img_url in urls:
            if img_url:
                # Append the URL to new description
                description += f"[url={img_url}][img=650]{img_url}[/img][/url]"

        missing = urls.count(None)
        if missing:
            custom_console.bot_error_log(f"{missing} of {len(urls)} screenshots not uploaded,"
                                         f" the description has only {len(urls) - missing}")

        # Append the new URL to the description string
        description += "\n[/center]"
        return description

