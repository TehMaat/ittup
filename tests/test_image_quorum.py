# -*- coding: utf-8 -*-
import pytest
import requests

from ittup.common import config_settings
from ittup.common.external_services import imageHost
from ittup.common.external_services.imageHost import (Build, ImgBB, Freeimage, ImageUploaderFallback,
                                                      ScreenshotsUploadFailed, UploadedImage)


@pytest.fixture
def hosts(monkeypatch, tmp_path):
    """ ImgBB (priority 0) and Freeimage (priority 1) with a key, the other hosts without """
    for key in ["IMGBB_KEY", "FREE_IMAGE_KEY", "LENSDUMP_KEY", "PTSCREENS_KEY", "IMGFI_KEY", "PASSIMA_KEY",
                "IMARIDE_KEY"]:
        monkeypatch.setattr(config_settings.tracker_config, key, "no_key")
    monkeypatch.setattr(config_settings.tracker_config, "IMGBB_KEY", "imgbb-key")
    monkeypatch.setattr(config_settings.tracker_config, "FREE_IMAGE_KEY", "freeimage-key")
    monkeypatch.setattr(ImgBB, "priority", 0)
    monkeypatch.setattr(Freeimage, "priority", 1)

    monkeypatch.setattr(imageHost, "SCREENSHOTS_TO_DELETE_PATH", tmp_path / "screenshots_to_delete.txt")

    state = {"online": {"ImgBB": True, "Freeimage": True}, "limit": {}, "uploads": [], "deleted": []}

    def upload(self):
        host = self.__class__.__name__
        done = [name for name in state["uploads"] if name[0] == host]
        if not state["online"][host] or len(done) >= state["limit"].get(host, 99):
            return None
        state["uploads"].append((host, self.image_name))
        url = f"https://{host}/{self.image_name}.png"
        if host == "ImgBB":
            return {"data": {"image": {"url": url}, "delete_url": url + "/delete"}}
        return {"image": {"image": {"url": url}, "url": url, "delete_url": url + "/delete"}}

    def delete(self, delete_url):
        state["deleted"].append(delete_url)
        return True

    monkeypatch.setattr(imageHost.ImageUploader, "upload", upload)
    monkeypatch.setattr(imageHost.ImageUploader, "delete", delete)
    return state


def test_every_screenshot_uploaded(hosts):
    description = Build(extracted_frames=[b"1", b"2", b"3", b"4"], filename="Movie").description()
    assert description.count("[img=650]") == 4
    assert {host for host, _ in hosts["uploads"]} == {"ImgBB"}
    assert hosts["deleted"] == []


def test_the_next_host_takes_over(hosts):
    # ImgBB fails after two screenshots: Freeimage uploads the others
    hosts["limit"]["ImgBB"] = 2
    description = Build(extracted_frames=[b"1", b"2", b"3", b"4"], filename="Movie").description()
    assert description.count("[img=650]") == 4
    assert [host for host, _ in hosts["uploads"]].count("Freeimage") == 2


def test_no_quorum_blocks_the_upload_and_removes_the_screenshots(hosts):
    hosts["online"]["ImgBB"] = False
    hosts["limit"]["Freeimage"] = 1
    with pytest.raises(ScreenshotsUploadFailed, match="only 1 of 4 screenshots"):
        Build(extracted_frames=[b"1", b"2", b"3", b"4"], filename="Movie").description()
    # The screenshot already uploaded is removed from the host
    assert len(hosts["deleted"]) == 1 and hosts["deleted"][0].startswith("https://Freeimage/")


def test_imgbb_screenshots_are_left_to_remove_by_hand(hosts):
    # ImgBB has no API to delete: its screenshots stay, with the delete link in the log
    hosts["limit"]["ImgBB"] = 1
    hosts["online"]["Freeimage"] = False
    with pytest.raises(ScreenshotsUploadFailed, match="only 1 of 4 screenshots"):
        Build(extracted_frames=[b"1", b"2", b"3", b"4"], filename="Movie").description()
    assert hosts["deleted"] == []
    # ... and in the file of the screenshots to remove by hand
    lines = imageHost.SCREENSHOTS_TO_DELETE_PATH.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert lines[0].split("\t")[1:] == ["Movie", "ImgBB", "https://ImgBB/Movie.id_1.png",
                                        "https://ImgBB/Movie.id_1.png/delete"]
    assert ImgBB(b"x", "key", image_name="Movie").delete("https://ibb.co/abc/hash") is False


def test_the_delete_link_of_the_response():
    assert ImageUploaderFallback.result({"data": {"image": {"url": "u"}, "delete_url": "d"}}, "ImgBB") == \
        UploadedImage(url="u", delete_url="d", host="ImgBB")
    assert ImageUploaderFallback.result({"image": {"url": "u"}}, "LensDump") == \
        UploadedImage(url="u", delete_url=None, host="LensDump")


class Response:
    def __init__(self, status_code, location=""):
        self.status_code = status_code
        self.headers = {"Location": location}
        self.is_redirect = 300 <= status_code < 400
        self.ok = status_code < 400


def test_chevereto_delete_link(monkeypatch):
    uploader = Freeimage(b"x", "key", image_name="Movie")
    monkeypatch.setattr(requests, "get", lambda *a, **k: Response(301, "https://freeimage.host/i/abc?deleted"))
    assert uploader.delete("https://freeimage.host/image/abc/delete/hash") is True
    monkeypatch.setattr(requests, "get", lambda *a, **k: Response(404))
    assert uploader.delete("https://freeimage.host/image/abc/delete/hash") is False
