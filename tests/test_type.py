# -*- coding: utf-8 -*-
import pytest

from ittup.common.trackers.trackers import TRACKData

ITT = TRACKData.load_from_module(tracker_name="ITT")


@pytest.mark.parametrize("name, type_id", [
    # The source wins over the codec and the generic tags written before it
    ("Movie.2020.1080p.HEVC.WEB-DL.DDP5.1-GRP.mkv", 4),
    ("Movie 2020 1080p FullHD WEB-DL H.264.mkv", 4),
    ("Movie.2020.1080p.BluRay.REMUX.AVC.DTS-HD.MA.5.1-GRP.mkv", 2),
    ("Movie.2020.2160p.UHD.BluRay.x265-GRP.mkv", 3),
    ("Movie.2020.1080p.WEBRip.x264-GRP.mkv", 5),
    ("Movie.2020.1080p.WEB-DLMux.H.264.mkv", 4),
    ("Movie.2020.1080p.DLMux.H.264.mkv", 27),
    ("Movie.2020.1080p.BDMux.x264.mkv", 29),
    ("Movie.2020.720p.HDTV.x264.mkv", 6),
    ("Movie.2020.1080p.Full.Disc.AVC", 1),
    # NFRip is a WEBRip
    ("Show.S01E01.1080p.NFRip.x264.mkv", 5),
    # Words of the title are not tags
    ("Charlotte's Web 2006 1080p BluRay x264.mkv", 3),
    ("Un altro giro 2020 1080p x264.mkv", 3),
    # No source: a codec means encode, nothing means 'altro'
    ("Movie.2020.1080p.x264.mkv", 3),
    ("Movie.2020.mkv", 15),
])
def test_type_from_the_source_in_the_name(name, type_id):
    assert ITT.filter_type(name) == type_id


def test_the_folder_name_comes_before_the_file_name():
    assert ITT.filter_type("Show S01 1080p NF WEB-DL H.264", "/upload/Show S01/Show.S01E01.x264.mkv") == 4


def test_the_file_name_is_used_when_the_folder_has_no_source():
    assert ITT.filter_type("Show S01", "/upload/Show S01 WEB-DL/Show.S01E01.1080p.WEBRip.mkv") == 5


def test_documents_use_the_extension():
    assert ITT.filter_type("/books/Magazine 2020.pdf") == 16
