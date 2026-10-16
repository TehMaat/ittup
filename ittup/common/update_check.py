# -*- coding: utf-8 -*-
import re
import threading

import requests

from ittup.common.about import PACKAGE_NAME, USER_AGENT, __version__

PYPI_URL = f"https://pypi.org/pypi/{PACKAGE_NAME}/json"
UPGRADE_DOCS_URL = "https://tehmaat.github.io/ittup/install/upgrade/"

# Seconds for the PyPI request
TIMEOUT = 3


def parse_version(value: str) -> tuple[int, ...] | None:
    """
    The release numbers of a version ('1.8.0' -> (1, 8, 0)), None for a pre-release or a local build
    """
    if not re.fullmatch(r"\d+(\.\d+)*", value or ""):
        return None
    return tuple(int(part) for part in value.split("."))


def is_newer(latest: str, current: str) -> bool:
    latest_numbers, current_numbers = parse_version(latest), parse_version(current)
    if latest_numbers is None or current_numbers is None:
        return False
    return latest_numbers > current_numbers


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
        # A source checkout (0.0.0+unknown) has no version to compare
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
