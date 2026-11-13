# -*- coding: utf-8 -*-
import pytest

from ittup.common import config_settings
from ittup.common.external_services import imageHost
from ittup.common.external_services.imageHost import Build, ImgBB, OnlyImage


class FakeResponse:
    def __init__(self, answer: dict):
        self.answer = answer

    def raise_for_status(self):
        pass

    def json(self) -> dict:
        return self.answer


@pytest.fixture
def keys(monkeypatch):
    """ OnlyImage and ImgBB with an API key, the other hosts without """
    for key in ("IMGBB_KEY", "FREE_IMAGE_KEY", "LENSDUMP_KEY", "PTSCREENS_KEY", "ONLYIMAGE_KEY", "PASSIMA_KEY",
                "IMARIDE_KEY"):
        monkeypatch.setattr(config_settings.tracker_config, key, "no_key")
    monkeypatch.setattr(config_settings.tracker_config, "ONLYIMAGE_KEY", "onlyimage-key")
    monkeypatch.setattr(config_settings.tracker_config, "IMGBB_KEY", "imgbb-key")
    monkeypatch.setattr(imageHost.time, "sleep", lambda seconds: None)


def test_onlyimage_uploads_to_its_api_and_reads_the_chevereto_answer(monkeypatch, keys):
    monkeypatch.setattr(OnlyImage, "priority", 0)
    monkeypatch.setattr(ImgBB, "priority", 1)
    requests_sent = []

    def post(url, data, files, timeout):
        requests_sent.append((url, data, files))
        return FakeResponse({"status_code": 200, "image": {"url": "https://onlyimage.org/images/video.id_1.png",
                                                            "delete_url": "https://onlyimage.org/delete/abc"}})

    monkeypatch.setattr(imageHost.requests, "post", post)

    image = Build([b"1"], "video").upload_image(1, b"1")

    assert image is not None
    assert (image.host, image.url, image.delete_url) == \
        ("OnlyImage", "https://onlyimage.org/images/video.id_1.png", "https://onlyimage.org/delete/abc")
    url, data, files = requests_sent[0]
    assert url == "https://onlyimage.org/api/1/upload"
    assert data["key"] == "onlyimage-key"
    assert "source" in files


def test_onlyimage_has_the_priority_of_the_config():
    assert OnlyImage.priority == config_settings.user_preferences.ONLYIMAGE_PRIORITY


@pytest.mark.parametrize("onlyimage_priority, first", [(0, OnlyImage), (2, ImgBB)])
def test_onlyimage_follows_its_priority(monkeypatch, keys, onlyimage_priority, first):
    monkeypatch.setattr(OnlyImage, "priority", onlyimage_priority)
    monkeypatch.setattr(ImgBB, "priority", 1)

    uploaders = Build([b"1"], "video").uploaders(b"1", image_name="video.id_1")

    assert [type(uploader) for uploader in uploaders][0] is first
    assert {type(uploader) for uploader in uploaders} == {OnlyImage, ImgBB}


def test_onlyimage_without_key_is_skipped(monkeypatch, keys):
    monkeypatch.setattr(config_settings.tracker_config, "ONLYIMAGE_KEY", "no_key")

    uploaders = Build([b"1"], "video").uploaders(b"1", image_name="video.id_1")

    assert [type(uploader) for uploader in uploaders] == [ImgBB]
