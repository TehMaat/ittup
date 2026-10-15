# -*- coding: utf-8 -*-
import pytest
import requests

from ittup.common import config_settings
from ittup.common.external_services import imageHost
from ittup.common.external_services.imageHost import Build, ScreenshotsUploadFailed, UPLOAD_ATTEMPTS


class FakeResponse:
    def __init__(self, url: str):
        self.url = url

    def raise_for_status(self):
        pass

    def json(self) -> dict:
        # The URL where ImgBB, Freeimage and the Chevereto hosts put it
        return {"data": {"image": {"url": self.url}}, "image": {"url": self.url, "image": {"url": self.url}}}


@pytest.fixture
def only_imgbb(monkeypatch, tmp_path):
    """ ImgBB is the only host with an API key, no wait between the attempts """
    for key in ("FREE_IMAGE_KEY", "LENSDUMP_KEY", "PTSCREENS_KEY", "IMGFI_KEY", "PASSIMA_KEY", "IMARIDE_KEY"):
        monkeypatch.setattr(config_settings.tracker_config, key, "no_key")
    monkeypatch.setattr(config_settings.tracker_config, "IMGBB_KEY", "imgbb-key")
    monkeypatch.setattr(imageHost.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(imageHost, "SCREENSHOTS_TO_DELETE_PATH", tmp_path / "screenshots_to_delete.txt")


def fake_post(monkeypatch, failures: dict[str, int], error=requests.exceptions.ReadTimeout):
    """
    requests.post that fails 'failures[name]' times for the screenshot 'name', then returns its URL

    :return: the number of requests for each screenshot
    """
    calls: dict[str, int] = {}

    def post(url, data, files, timeout):
        name = data["name"]
        calls[name] = calls.get(name, 0) + 1
        if calls[name] <= failures.get(name, 0):
            raise error()
        return FakeResponse(f"https://i.ibb.co/{name}.png")

    monkeypatch.setattr(imageHost.requests, "post", post)
    return calls


def test_a_timeout_is_retried(monkeypatch, only_imgbb):
    calls = fake_post(monkeypatch, {"video.id_1": 1})
    description = Build([b"1", b"2"], "video").description()
    assert "https://i.ibb.co/video.id_1.png" in description
    assert "https://i.ibb.co/video.id_2.png" in description
    assert calls["video.id_1"] == 2


def test_a_connection_error_is_retried(monkeypatch, only_imgbb):
    fake_post(monkeypatch, {"video.id_1": 2}, error=requests.exceptions.ConnectionError)
    assert "https://i.ibb.co/video.id_1.png" in Build([b"1"], "video").description()


def test_a_screenshot_is_lost_after_every_attempt(monkeypatch, only_imgbb):
    calls = fake_post(monkeypatch, {"video.id_1": UPLOAD_ATTEMPTS})
    # Without every screenshot the content is not uploaded
    with pytest.raises(ScreenshotsUploadFailed, match="only 1 of 2 screenshots"):
        Build([b"1", b"2"], "video").description()
    assert calls["video.id_1"] == UPLOAD_ATTEMPTS


def test_the_only_host_is_tried_after_failing_a_screenshot(monkeypatch, only_imgbb):
    # One screenshot at a time: the first one marks ImgBB off-line before the second one starts
    monkeypatch.setattr(imageHost, "UPLOAD_WORKERS", 1)
    calls = fake_post(monkeypatch, {"video.id_1": UPLOAD_ATTEMPTS})
    with pytest.raises(ScreenshotsUploadFailed, match="only 2 of 3 screenshots"):
        Build([b"1", b"2", b"3"], "video").description()
    assert calls["video.id_2"] == 1 and calls["video.id_3"] == 1


def test_a_failed_host_is_not_skipped_by_the_next_upload(monkeypatch, only_imgbb):
    fake_post(monkeypatch, {"first.id_1": UPLOAD_ATTEMPTS})
    with pytest.raises(ScreenshotsUploadFailed):
        Build([b"1"], "first").description()
    assert "https://i.ibb.co/second.id_1.png" in Build([b"1"], "second").description()


def http_error(status: int):
    """ The error raised by raise_for_status() for an answer with this status """
    response = requests.Response()
    response.status_code = status
    response._content = b'{"status_code": %d, "error": {"message": "error"}}' % status
    return lambda: requests.exceptions.HTTPError(response=response)


def test_a_server_error_is_retried(monkeypatch, only_imgbb):
    calls = fake_post(monkeypatch, {"video.id_1": 1}, error=http_error(503))
    assert "https://i.ibb.co/video.id_1.png" in Build([b"1"], "video").description()
    assert calls["video.id_1"] == 2


def test_a_bad_request_is_not_retried(monkeypatch, only_imgbb):
    # e.g. the screenshot is too big: it fails again
    calls = fake_post(monkeypatch, {"video.id_1": 1}, error=http_error(400))
    with pytest.raises(ScreenshotsUploadFailed):
        Build([b"1"], "video").description()
    assert calls["video.id_1"] == 1


def test_an_off_line_host_is_tried_after_the_other_ones(monkeypatch, only_imgbb):
    monkeypatch.setattr(config_settings.tracker_config, "FREE_IMAGE_KEY", "freeimage-key")
    monkeypatch.setattr(imageHost.Freeimage, "priority", 0)
    monkeypatch.setattr(imageHost.ImgBB, "priority", 1)
    monkeypatch.setattr(imageHost, "UPLOAD_WORKERS", 1)
    hosts = []

    def post(url, data, files, timeout):
        hosts.append((data["name"], url))
        # Freeimage loses the first screenshot, ImgBB the second one
        if (data["name"], "freeimage" in url) in (("video.id_1", True), ("video.id_2", False)):
            raise requests.exceptions.ConnectionError()
        return FakeResponse(f"https://{data['name']}.png")

    monkeypatch.setattr(imageHost.requests, "post", post)
    description = Build([b"1", b"2"], "video").description()
    assert "https://video.id_1.png" in description
    assert "https://video.id_2.png" in description
    # Freeimage is off-line after the first screenshot, but it's still tried when ImgBB fails the second one
    assert [url for name, url in hosts if name == "video.id_2"][-1] == "https://freeimage.host/api/1/upload"


def test_an_answer_without_the_url_loses_only_its_screenshot(monkeypatch, only_imgbb):
    def post(url, data, files, timeout):
        response = FakeResponse(f"https://i.ibb.co/{data['name']}.png")
        if data["name"] == "video.id_1":
            response.json = lambda: {"data": {}}
        return response

    monkeypatch.setattr(imageHost.requests, "post", post)
    images = [Build([b"1", b"2"], "video").safe_upload_image(number, b"x") for number in (1, 2)]
    assert images[0] is None
    assert images[1].url == "https://i.ibb.co/video.id_2.png"
