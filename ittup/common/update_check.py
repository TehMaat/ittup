# -*- coding: utf-8 -*-
import re
import threading
from importlib.metadata import PackageNotFoundError, version as package_version

import requests

from ittup.common.about import PACKAGE_NAME, USER_AGENT, __version__

PYPI_URL = f"https://pypi.org/pypi/{PACKAGE_NAME}/json"
UPGRADE_DOCS_URL = "https://tehmaat.github.io/ittup/install/upgrade/"

# Seconds for the PyPI request
TIMEOUT = 3


# A release or a pre-release (PEP 440): '1.13.0', '1.13.0rc3', '1.13.0b1', '1.13.0a2'
VERSION = re.compile(r"(\d+(?:\.\d+)*)(?:(a|b|rc)(\d+))?")
# The pre-releases come before their release: 1.13.0a1 < 1.13.0b1 < 1.13.0rc1 < 1.13.0
PRE_RELEASE = {"a": 0, "b": 1, "rc": 2}
RELEASE = len(PRE_RELEASE)


def parse_version(value: str) -> tuple[tuple[int, ...], int, int] | None:
    """
    A key that sorts the versions ('1.13.0rc3' -> ((1, 13), 2, 3)), None for a dev or a local build
    """
    match = VERSION.fullmatch(value or "")
    if not match:
        return None
    numbers, pre_release, pre_number = match.groups()
    release = tuple(int(part) for part in numbers.split("."))
    # 1.13 is 1.13.0
    while len(release) > 1 and release[-1] == 0:
        release = release[:-1]
    if pre_release:
        return release, PRE_RELEASE[pre_release], int(pre_number)
    return release, RELEASE, 0


def is_newer(latest: str, current: str) -> bool:
    """
    'latest' is a release newer than 'current'. 'current' can be a pre-release (an rc installed with --pre),
    'latest' never is: a pre-release on PyPI is not an upgrade, the testers install it by hand
    """
    latest_key, current_key = parse_version(latest), parse_version(current)
    if latest_key is None or current_key is None or latest_key[1] != RELEASE:
        return False
    return latest_key > current_key


def latest_version() -> str | None:
    """
    The latest version on PyPI, None when PyPI doesn't answer
    """
    try:
        response = requests.get(PYPI_URL, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()["info"]["version"]
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return None


def installed_version() -> str | None:
    """
    The version installed now, which differs from __version__ when the package has been upgraded since
    the start. None in a source checkout
    """
    try:
        return package_version(PACKAGE_NAME)
    except PackageNotFoundError:
        return None


class UpdateCheck:
    """
    Asks PyPI for the latest version in the background, while the bot starts
    """

    def __init__(self, current: str = __version__):
        self.current = current
        self.latest: str | None = None
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        self.latest = latest_version()

    def start(self) -> "UpdateCheck":
        # A source checkout (0.0.0+unknown) or a dev build (1.12.2.dev812) has no version to compare
        if parse_version(self.current) is not None:
            self._thread.start()
        return self

    def newer_version(self, wait: float = 1) -> str | None:
        """
        The newer version on PyPI, None if there is none or PyPI didn't answer within 'wait' seconds
        """
        if self._thread.ident is not None:
            self._thread.join(timeout=wait)
        if self.latest and is_newer(self.latest, self.current):
            return self.latest
        return None
