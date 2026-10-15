import pprint
import re
from argparse import Namespace
import requests
import json

from ittup.common.external_services.igdb.core.models.search import Game
from ittup.common.trackers.trackers import TRACKData
from ittup.common.about import APP_NAME, REPO_URL

from ittup.core.pvtTracker import Unit3d
from ittup.core.pvtDocu import PdfImages
from ittup.core import config_settings, Load
from ittup.core.pvtVideo import Video
from ittup.core.media import Media

from ittup.view import custom_console


class UploadBot:
    def __init__(self, content: Media, tracker_name: str, cli: Namespace):
        self.cli = cli
        self.content = content
        self.tracker_name = tracker_name
        self.tracker_data = TRACKData.load_from_module(tracker_name=tracker_name)
        self.tracker = Unit3d(tracker_name=tracker_name)
        self.sign = (
            f"[quote][url={REPO_URL}][color=#00BFFF][size=14]Uploaded with {APP_NAME}"
            f" v{Load.version}[/size][/color][/url][/quote]")

    def message(self, tracker_response: requests.Response, torrent_archive: str):

        name_error = ''
        info_hash_error = ''
        _message = json.loads(tracker_response.text)
        if 'data' in _message:
            _message = _message['data']

        if tracker_response.status_code == 200:
            tracker_response_body = json.loads(tracker_response.text)
            custom_console.bot_log(
                f"\n[RESPONSE]-> '{self.tracker_name}'.....{tracker_response_body['message'].upper()}\n\n")
            custom_console.rule()
            # https://github.com/HDInnovations/UNIT3D/pull/4910/files
            # 08/09/2025
            # We have to download the torrent file to get the new random info_hash generated
            self.download_file(url=tracker_response_body["data"], destination_path=torrent_archive)
            self.check_flags(download_url=tracker_response_body["data"])
            return tracker_response_body["data"], {}

        elif tracker_response.status_code == 401:
            custom_console.bot_error_log(_message)
            exit(_message['message'])

        elif tracker_response.status_code == 403:
            error_message = f"{self.__class__.__name__} HTTP 403 Upload right disabled"
            custom_console.bot_error_log(self.content.file_name)

        elif tracker_response.status_code == 404:
            error_message = f"{self.__class__.__name__} - {_message}"

        elif tracker_response.status_code == 500:
            custom_console.bot_error_log(f"{self.__class__.__name__} HTTP 500 Internal Tracker Error\n")
            pprint.pprint(self.tracker.data)
            custom_console.bot_error_log(self.content.file_name)
            exit()

        else:
            if _message.get("name", None):
                name_error = _message["name"][0]
            if _message.get("info_hash", None):
                info_hash_error = _message["info_hash"][0]
            error_message = f"{self.__class__.__name__} - {name_error} : {info_hash_error}"

        custom_console.bot_error_log(f"\n[RESPONSE]-> '{error_message}\n\n")
        custom_console.rule()
        return {}, error_message

    def check_flags(self, download_url: str) -> None:
        """
        The tracker applies -int and -fl25..-fl100 only if the account can set them (staff or internal group),
        otherwise it uploads the torrent without them and doesn't say it: read the torrent back and warn
        """
        internal = bool(int(self.tracker.data.get("internal") or 0))
        free = int(self.tracker.data.get("free") or 0)
        if not internal and not free:
            return

        match = re.search(r"/download/(\d+)", str(download_url))
        if not match:
            return
        try:
            body = self.tracker.fetch_id(int(match.group(1))).json()
            attributes = body.get("data", body)["attributes"]
        except (requests.RequestException, ValueError, KeyError, TypeError, AttributeError):
            custom_console.bot_warning_log("Can't read the uploaded torrent to check -int and the freeleech")
            return

        if internal and not int(attributes.get("internal") or 0):
            custom_console.bot_warning_log(
                f"-int: '{self.tracker_name}' didn't upload the torrent as an internal release."
                f" Only staff and the members of an internal group can set it")
        applied_free = int(re.sub(r"\D", "", str(attributes.get("freeleech") or "")) or 0)
        if free and applied_free != free:
            custom_console.bot_warning_log(
                f"-fl{free}: '{self.tracker_name}' set the freeleech to {applied_free}% instead of {free}%."
                f" Only staff and the members of an internal group can set it")

    def internal(self) -> int:
        """ 1 with the -int flag: upload as an internal release """
        return int(bool(getattr(self.cli, "internal", False)))

    def freeleech(self) -> int:
        """ Freeleech percentage from the -fl25, -fl50, -fl75, -fl100 flags, 0 without them """
        return int(getattr(self.cli, "freeleech", None) or 0)

    def resolution_id(self) -> int | None:
        value = self.content.resolution
        _id = self.tracker_data.resolution.get(value)
        if not _id:
            custom_console.bot_error_log(f"Resolution ID {value} not found")
        return _id

    def category_id(self) -> int | None:
        _id = self.tracker_data.category.get(self.content.category)
        if not _id:
            custom_console.bot_error_log(f"Category ID {self.content.category} not found")
        return _id


    def data(self, show_id: int, imdb_id: int, tvdb_id: int, show_keywords_list: str,
             video_info: Video) -> Unit3d | None:

        self.tracker.data["name"] = self.content.display_name
        self.tracker.data["tmdb"] = show_id
        self.tracker.data["imdb"] = imdb_id if imdb_id else 0
        self.tracker.data["tvdb"] = tvdb_id if tvdb_id and self.content.category == 'tv' else None
        self.tracker.data["keywords"] = show_keywords_list
        self.tracker.data["category_id"] = self.tracker_data.category.get(self.content.category)
        self.tracker.data["anonymous"] = int(config_settings.user_preferences.ANON)
        self.tracker.data["mediainfo"] = video_info.mediainfo
        self.tracker.data["description"] = video_info.description + self.sign
        self.tracker.data["sd"] = video_info.is_hd
        # The source in the release name decides the type: the folder name first, then the video file name
        self.tracker.data["type_id"] = self.tracker_data.filter_type(self.content.torrent_name, self.content.file_name)
        self.tracker.data["season_number"] = self.content.guess_season
        self.tracker.data["episode_number"] = (self.content.guess_episode if not self.content.torrent_pack else 0)
        self.tracker.data["personal_release"] = (int(config_settings.user_preferences.PERSONAL_RELEASE)
                                                 or int(self.cli.personal))
        self.tracker.data["internal"] = self.internal()
        self.tracker.data["free"] = self.freeleech()
        self.tracker.data["mod_queue_opt_in"] = int(self.cli.moderation)


        # skip upload if the key is missing
        if self.category_id():
            self.tracker.data["category_id"] = self.category_id()
        else:
            return None

        if self.resolution_id():
            self.tracker.data["resolution_id"] = self.resolution_id()
        else:
            return None

        return self.tracker

    def data_game(self, igdb: Game) -> Unit3d | None:

        igdb_platform = self.content.platform_list[0].lower() if self.content.platform_list else ''
        self.tracker.data["name"] = self.content.display_name
        self.tracker.data["tmdb"] = 0
        self.tracker.data["category_id"] = self.tracker_data.category.get(self.content.category)
        self.tracker.data["anonymous"] = int(config_settings.user_preferences.ANON)
        self.tracker.data["description"] = igdb.description + self.sign if igdb else "Sorry, there is no valid IGDB"
        self.tracker.data["type_id"] = self.tracker_data.type_id.get(igdb_platform) if igdb_platform else 1
        self.tracker.data["igdb"] = igdb.id if igdb else 1  # need zero not one ( fix tracker)
        self.tracker.data["internal"] = self.internal()
        self.tracker.data["free"] = self.freeleech()
        self.tracker.data["personal_release"] = (int(config_settings.user_preferences.PERSONAL_RELEASE)
                                                 or int(self.cli.personal))
        return self.tracker

    def data_docu(self, document_info: PdfImages) -> Unit3d | None:

        self.tracker.data["name"] = self.content.display_name
        self.tracker.data["tmdb"] = 0
        self.tracker.data["category_id"] = self.tracker_data.category.get(self.content.category)
        self.tracker.data["anonymous"] = int(config_settings.user_preferences.ANON)
        self.tracker.data["description"] = document_info.description + self.sign
        self.tracker.data["type_id"] = self.tracker_data.filter_type(self.content.file_name)
        self.tracker.data["resolution_id"] = ""
        self.tracker.data["internal"] = self.internal()
        self.tracker.data["free"] = self.freeleech()
        self.tracker.data["personal_release"] = (int(config_settings.user_preferences.PERSONAL_RELEASE)
                                                 or int(self.cli.personal))
        return self.tracker

    def send(self, torrent_archive: str, nfo_path=None):

        tracker_response = self.tracker.upload_t(data=self.tracker.data, torrent_archive_path=torrent_archive,
                                                 nfo_path=nfo_path)

        return self.message(tracker_response=tracker_response, torrent_archive=torrent_archive)

    @staticmethod
    def download_file(url: str, destination_path: str) -> bool:
        download = requests.get(url)
        if download.status_code == 200:
            # File archived
            with open(destination_path, "wb") as file:
                file.write(download.content)
            return True
        return False
