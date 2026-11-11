# -*- coding: utf-8 -*-
import pytest
import requests

from ittup.common import update_check
from ittup.common.update_check import UpdateCheck, is_newer


@pytest.mark.parametrize("latest, current, newer", [
    ("1.9.0", "1.8.0", True),
    ("1.10.0", "1.9.0", True),
    ("2.0", "1.9.9", True),
    ("1.8.0", "1.8.0", False),
    ("1.7.0", "1.8.0", False),
    ("1.9.0rc1", "1.8.0", False),
    ("1.9.0", "0.0.0+unknown", False),
    ("2.0.0", "2.0", False),
    # #120: an rc installed gets the release after it, never another pre-release
    ("1.13.0", "1.13.0rc3", True),
    ("1.13.1", "1.13.0rc3", True),
    ("1.13.0", "1.13.0b2", True),
    ("1.12.1", "1.13.0rc3", False),
    ("1.13.0rc3", "1.13.0rc3", False),
    ("1.13.0rc4", "1.13.0rc3", False),
    ("1.14.0rc1", "1.13.0", False),
    # A dev build is not compared
    ("1.13.0", "1.12.2.dev812", False),
])
def test_is_newer(latest, current, newer):
    assert is_newer(latest, current) is newer


class Response:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


def test_a_newer_version_on_pypi_is_reported(monkeypatch):
    monkeypatch.setattr(update_check.requests, "get", lambda *args, **kwargs: Response({"info": {"version": "9.0.0"}}))

    assert UpdateCheck(current="1.8.0").start().newer_version() == "9.0.0"


def test_the_release_of_an_installed_rc_is_reported(monkeypatch):
    monkeypatch.setattr(update_check.requests, "get", lambda *args, **kwargs: Response({"info": {"version": "1.13.0"}}))

    assert UpdateCheck(current="1.13.0rc3").start().newer_version() == "1.13.0"


def test_the_installed_version_is_not_reported(monkeypatch):
    monkeypatch.setattr(update_check.requests, "get", lambda *args, **kwargs: Response({"info": {"version": "1.8.0"}}))

    assert UpdateCheck(current="1.8.0").start().newer_version() is None


def test_pypi_offline_is_not_an_error(monkeypatch):
    def offline(*args, **kwargs):
        raise requests.ConnectionError("offline")
    monkeypatch.setattr(update_check.requests, "get", offline)

    assert UpdateCheck(current="1.8.0").start().newer_version() is None


def test_a_source_checkout_does_not_ask_pypi(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("PyPI asked")
    monkeypatch.setattr(update_check.requests, "get", fail)

    assert UpdateCheck(current="0.0.0+unknown").start().newer_version() is None
