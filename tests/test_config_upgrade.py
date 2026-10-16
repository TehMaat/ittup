# -*- coding: utf-8 -*-
import json

import pytest

from ittup.common.settings import (Config, JsonConfig, Load, TrackerConfig, TorrentClientConfig, UserPreferences,
                                   Options, ConsoleOptions)

MODELS = {
    "tracker_config": TrackerConfig,
    "torrent_client_config": TorrentClientConfig,
    "user_preferences": UserPreferences,
    "options": Options,
    "console_options": ConsoleOptions,
}


def write(path, data):
    path.write_text(json.dumps(data, indent=4), encoding="utf-8")
    return path


def old_config():
    """
    A config file of an older version: a few attributes missing, one left empty, one obsolete, another order
    """
    config = Load.default_config()
    preferences = config["user_preferences"]
    del preferences["CHECK_CORRUPTED_START"]
    del preferences["CHECK_CORRUPTED_IGNORE_DV"]
    del config["torrent_client_config"]["QBIT_ENABLED"]
    preferences["CHECK_CORRUPTED_END"] = ""
    preferences["NUMBER_OF_SCREENSHOTS"] = 6
    preferences["OLD_FLAG"] = "True"
    config["torrent_client_config"]["QBIT_PORT"] = ""
    config["tracker_config"] = dict(reversed(list(config["tracker_config"].items())))
    config["tracker_config"]["ITT_APIKEY"] = "my_key"
    return config


@pytest.mark.parametrize("section", MODELS)
def test_the_default_config_has_every_attribute_of_the_models(section):
    assert set(Load.default_config()[section]) == set(MODELS[section].model_fields)


def test_the_config_is_rebuilt_with_the_user_values_and_the_new_defaults(tmp_path):
    path = write(tmp_path / "ittup.json", old_config())

    data = JsonConfig(path).process()

    defaults = Load.default_config()
    assert [list(section) for section in data.values()] == [list(section) for section in defaults.values()]
    preferences = data["user_preferences"]
    assert preferences["NUMBER_OF_SCREENSHOTS"] == 6
    assert preferences["CHECK_CORRUPTED_START"] == defaults["user_preferences"]["CHECK_CORRUPTED_START"]
    assert preferences["CHECK_CORRUPTED_IGNORE_DV"] == defaults["user_preferences"]["CHECK_CORRUPTED_IGNORE_DV"]
    assert preferences["CHECK_CORRUPTED_END"] == defaults["user_preferences"]["CHECK_CORRUPTED_END"]
    assert "OLD_FLAG" not in preferences
    assert data["torrent_client_config"]["QBIT_ENABLED"] == "True"
    # An empty QBIT_PORT is a reverse proxy, not a missing value
    assert data["torrent_client_config"]["QBIT_PORT"] == ""
    assert data["tracker_config"]["ITT_APIKEY"] == "my_key"
    assert json.loads(path.read_text(encoding="utf-8")) == data

    backups = list(tmp_path.glob("ittup.json.bak-*"))
    assert len(backups) == 1
    assert json.loads(backups[0].read_text(encoding="utf-8")) == old_config()


def test_an_up_to_date_config_is_not_rewritten(tmp_path):
    path = write(tmp_path / "ittup.json", Load.default_config())
    JsonConfig(path).process()

    JsonConfig(path).process()

    assert not list(tmp_path.glob("ittup.json.bak-*"))


def test_the_lowercase_attributes_keep_their_value(tmp_path):
    config = Load.default_config()
    del config["user_preferences"]["SIZE_TH"]
    config["user_preferences"]["size_th"] = 99
    path = write(tmp_path / "ittup.json", config)

    data = JsonConfig(path).process()

    assert data["user_preferences"]["SIZE_TH"] == 99
    assert "size_th" not in data["user_preferences"]


def test_the_rebuilt_config_is_valid(tmp_path):
    path = write(tmp_path / "ittup.json", old_config())

    config = Config(**JsonConfig(path).process())

    assert config.user_preferences.CHECK_CORRUPTED_START == 10
    assert config.user_preferences.CHECK_CORRUPTED_END == 90
    assert config.user_preferences.CHECK_CORRUPTED_IGNORE_DV is False
    assert config.torrent_client_config.QBIT_ENABLED is True


@pytest.mark.parametrize("missing", [True, False])
def test_the_screenshot_options_get_the_default_value(tmp_path, missing):
    config = Load.default_config()
    for field in ("TIMEOUT_SCSHOT", "TONEMAP_SCSHOT"):
        if missing:
            del config["user_preferences"][field]
        else:
            # Added with an empty value by the older versions
            config["user_preferences"][field] = ""
    path = write(tmp_path / "ittup.json", config)

    data = JsonConfig(path).process()

    saved = json.loads(path.read_text(encoding="utf-8"))["user_preferences"]
    assert (saved["TIMEOUT_SCSHOT"], saved["TONEMAP_SCSHOT"]) == (120, "False")
    preferences = Config(**data).user_preferences
    assert (preferences.TIMEOUT_SCSHOT, preferences.TONEMAP_SCSHOT) == (120, False)
