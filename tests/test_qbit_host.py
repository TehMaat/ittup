# -*- coding: utf-8 -*-
import pytest

from ittup.common.settings import Validate


@pytest.mark.parametrize("host", [
    "127.0.0.1",
    "http://localhost",
    "192.168.1.10:8080",
    "::1",
    "seedbox.example.com",
    "casenol.seedhost.eu/torrent/",
    "https://casenol.seedhost.eu/torrent/",
    "http://my-nas.local:8080/qbittorrent",
])
def test_a_host_ip_or_fqdn_is_accepted(host):
    assert Validate.host(host, "QBIT_HOST", default_value="127.0.0.1") == host


def test_an_empty_host_is_the_default():
    assert Validate.host("", "QBIT_HOST", default_value="127.0.0.1") == "127.0.0.1"


@pytest.mark.parametrize("host", ["bad host", "-seedbox.com", "seed_box.com", "ftp:/x", "host:port", "host/?a=1"])
def test_an_invalid_host_is_refused(host):
    with pytest.raises(SystemExit):
        Validate.host(host, "QBIT_HOST", default_value="127.0.0.1")
