# -*- coding: utf-8 -*-
import pytest

from ittup.common.tags import SearchTags
from ittup.common.trackers.signs_list import SIGNS_LIST


@pytest.mark.parametrize("name, sign", [
    # 'IDN-CREW' is in the list: an underscore in the name must not leave only 'CreW'
    ("The Isolate Thief (2026) WEB-DL 2160p H265 10Bit Ita Eng Ac3 5.1 Sub - iDN_CreW.mkv", "-iDN_CreW"),
    ("Movie.2020.1080p.WEB-DL.H264-iDN-CreW.mkv", "-iDN-CreW"),
    ("Movie 2020 1080p WEB-DL H264 iDN CreW.mkv", "-iDN CreW"),
    ("Movie.2020.1080p.BluRay.x264-ARTEMIX.MIRCREW.mkv", "-ARTEMIX.MIRCREW"),
    ("Movie.2020.1080p.BluRay.x264-MIRCrew.mkv", "-MIRCrew"),
    ("Movie.2020.1080p.BluRay.x264-CreW.mkv", "-CreW"),
    # The sign must be at the end of the name
    ("Crew.2020.1080p.WEB-DL.H264-UNKNOWN.mkv", ""),
])
def test_detect_releaser(name, sign):
    assert SearchTags.detect_releaser(name, SIGNS_LIST) == sign


def test_a_sign_appearing_earlier_is_still_found_at_the_end():
    assert SearchTags.detect_releaser("Crew.Movie.2020.1080p-CreW.mkv", {"CREW": "releaser"}) == "-CreW"


def test_a_sign_made_only_of_separators_matches_nothing():
    assert SearchTags.detect_releaser("Movie.2020.1080p-GRP.mkv", {"-": "releaser", " ": "releaser"}) == ""
