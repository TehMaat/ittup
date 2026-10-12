# -*- coding: utf-8 -*-

from ittup.common import config_settings


def _base_url(url: str | None) -> str | None:
    # Drop any trailing slash so the announce URL never contains '//'
    return url.rstrip('/') if url else url


trackers_api_data = {
    'ITT':
        {
            "url": _base_url(config_settings.tracker_config.ITT_URL),
            "api_key": config_settings.tracker_config.ITT_APIKEY,
            "pass_key": config_settings.tracker_config.ITT_PID,
            "announce": f"{_base_url(config_settings.tracker_config.ITT_URL)}/announce/{config_settings.tracker_config.ITT_PID}",
            "source": "ItaTorrents",
        }

}

