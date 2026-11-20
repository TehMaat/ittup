# -*- coding: utf-8 -*-
from types import SimpleNamespace

import pytest

from ittup.common.tags import SearchTags
from ittup.common.trackers.tags_list import TAGS_LIST

POSITION = ["title", "year", "version", "platform", "source", "remux"]


def search(filename: str, tags_list: dict | None = None) -> SearchTags:
    mediafile = SimpleNamespace(general_track={}, video_track=[{"format": "AVC"}], audio_track=[], subtitle_track=[])
    media = SimpleNamespace(mediafile=mediafile, torrent_pack=False, resolution="1080p", pack=None)
    return SearchTags(filename=filename, title="Movie", year=2020, season=None, episode=None, media=media,
                      tags_position=list(POSITION), tags_list=tags_list or TAGS_LIST, sign_list={},
                      ban_list={"dummy": "banned"}, releaser_sign="")


@pytest.mark.parametrize("filename, expected", [
    # The version tags as the tags list writes them, whatever the case of the file name
    ("Movie.2020.Repack.1080p.WEB-DL.H264-GRP.mkv", "Movie 2020 REPACK WEB-DL"),
    ("Movie.2020.repack.1080p.WEB-DL.H264-GRP.mkv", "Movie 2020 REPACK WEB-DL"),
    ("Movie.2020.REPACK.1080p.WEB-DL.H264-GRP.mkv", "Movie 2020 REPACK WEB-DL"),
    ("Movie.2020.Remastered.1080p.BluRay.x264-GRP.mkv", "Movie 2020 REMASTERED BluRay"),
    ("Movie.2020.proper.1080p.WEB-DL.H264-GRP.mkv", "Movie 2020 PROPER WEB-DL"),
    ("Movie.2020.Extended.Uncut.1080p.Bdrip.x264-GRP.mkv", "Movie 2020 EXTENDED UNCUT BDRip"),
    # The other categories too
    ("Movie.2020.1080p.BluRay.Remux.AVC-GRP.mkv", "Movie 2020 BluRay REMUX"),
    ("Movie.2020.1080p.Bdremux.AVC-GRP.mkv", "Movie 2020 BDREMUX"),
    ("Movie.2020.1080p.Dlmux.H264-GRP.mkv", "Movie 2020 DLMUX REMUX"),
    ("Movie.2020.1080p.Nf.webrip.x264-GRP.mkv", "Movie 2020 NF WEBRip"),
    ("Movie.2020.1080p.Dvd9-GRP.mkv", "Movie 2020 DVD9"),
    # One WEB-DL: 'Web-DL' and 'WEB' are the same source
    ("Movie.2020.1080p.Amzn.Web-DL.H264-GRP.mkv", "Movie 2020 AMZN WEB-DL"),
    # The tags of TAG_NORMALIZE keep their spelling
    ("Movie.2020.1080p.bluray.x264-GRP.mkv", "Movie 2020 BluRay"),
    ("Movie.2020.1080p.Webmux.H264-GRP.mkv", "Movie 2020 WEBMux"),
])
def test_the_title_writes_the_tags_as_the_tags_list(filename, expected):
    assert search(filename).process()[0] == expected


@pytest.mark.parametrize("filename, release_type", [
    ("Movie.2020.1080p.BluRay.Remux.AVC-GRP.mkv", "untouched"),
    ("Movie.2020.1080p.Dlmux.H264-GRP.mkv", "web"),
    ("Movie.2020.1080p.Amzn.Web-DL.H264-GRP.mkv", "web"),
    ("Movie.2020.1080p.Nf.webrip.x264-GRP.mkv", "encode"),
])
def test_the_case_of_the_name_does_not_change_the_release_type(filename, release_type):
    for name in (filename, filename.lower(), filename.upper()):
        tags = search(name)
        tags.process()
        assert tags.release_type == release_type


def test_a_custom_tags_list_decides_the_spelling():
    tags_list = {"Repack": "version", "WEB-DL": "source"}
    assert search("Movie.2020.REPACK.1080p.web-dl.mkv", tags_list).process()[0] == "Movie 2020 Repack WEB-DL"
