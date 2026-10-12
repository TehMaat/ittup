# -*- coding: utf-8 -*-
from importlib.metadata import PackageNotFoundError, version as _package_version

# Package and command name
PACKAGE_NAME = "ittup"
# Name shown in logs, in the upload description and in the torrent "created by" field
APP_NAME = "ITTup"
APP_DESCRIPTION = "ItaTorrents uploader"
REPO_URL = "https://github.com/TehMaat/ittup"

# The version is defined only in pyproject.toml and read from the installed package metadata
try:
    __version__ = _package_version(PACKAGE_NAME)
except PackageNotFoundError:
    # Running from a source checkout without installing the package
    __version__ = "0.0.0+unknown"

USER_AGENT = f"{PACKAGE_NAME}/{__version__} (+{REPO_URL})"
