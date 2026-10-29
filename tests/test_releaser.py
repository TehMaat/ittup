# -*- coding: utf-8 -*-
import argparse
import sys

import pytest

from ittup.common import settings
from ittup.common.tags import SearchTags


@pytest.mark.parametrize("name, releaser", [
    # #112: the release group after a dot, a dash in the group, a group with a space
    ("Undertone.Sottofondo.2025.FULL.HD.1080p.VU.REMUX.TrueHD.ENG.E-AC3.ITA.AC3.ITA.ENG.SUBS.AVC.LFi.mkv", "-LFi"),
    ("Amore.sotto.copertura.S01E03.Episodio.3.1080p.WEB-DL.E-AC3.ITA.KOR.SUBS.H.264-S-K.mkv", "-S-K"),
    ("Amore.sotto.copertura.S01E03.Episodio.3.1080p.WEB-DL.E-AC3.ITA.KOR.SUBS.H.264.S-K.mkv", "-S-K"),
    ("Lo squalo - Jaws 3 (1983) AC3 5.1 ITA 2.0 ENG 1080p H265 sub ita.eng Sp33dy94-MIRCrew.mkv",
     "-Sp33dy94-MIRCrew"),
    ("Three Thousand Years of Longing (2022) iTA-ENG.Bluray.1080p.x264-Dr4gon MIRCrew.mkv", "-Dr4gon MIRCrew"),
    ("Film 2024 1080p ITA-ENG H264 - mircrew.mkv", "-mircrew"),
    ("Film.2024.1080p.WEB-DL.DDP5.1.H.264-NAHOM.mkv", "-NAHOM"),
    ("Il.Gladiatore.2.2024.2160p.UHD.BluRay.REMUX.HDR.HEVC.TrueHD.ITA.ENG-[HD4ME].mkv", "-HD4ME"),
    # A folder: no extension, '.GP' is part of the group
    ("Serie.S01.1080p.WEB-DL.ITA.ENG.SUBS-MeM.GP", "-MeM.GP"),
    ("Amore.sotto.copertura.S01.1080p.WEB-DL.E-AC3.ITA.KOR.SUBS.H.264.S-K", "-S-K"),
    # Not a release group: a word of the title, a language, MULTI, no group at all
    ("Spider-Man.2002.1080p.BluRay.x264.mkv", ""),
    ("Film.2024.1080p.BluRay.x264.AC3.ITA-ENG.mkv", ""),
    ("Film.2024.DVDRip.XviD-iTA-ENG.avi", ""),
    ("Film.2024.1080p.WEB-DL.H264-iTA.mkv", ""),
    ("Film.2024.1080p.WEB-DL.ITA.ENG.SUB-ITA.mkv", ""),
    ("Film.2024.1080p.WEB-DL.ITA.AAC.H264-MULTI.mkv", ""),
    # A tag of the title
    ("Titolo.1990.1080p.REMUX.VU.mkv", ""),
    ("Titolo 1990 1080p Remux vu.mkv", ""),
    ("Film.2024.1080p.WEB-DL.H264.ITA.ENG.SUBS.mkv", ""),
    ("Film.2024.1080p.BluRay.x264.DTS-HD.MA.5.1.mkv", ""),
])
def test_the_releaser_of_the_file_name(name, releaser):
    assert SearchTags.detect_releaser(name) == releaser


def test_the_releasers_list_reads_what_guessit_misses(monkeypatch):
    monkeypatch.setattr("ittup.common.tags.guessit.guessit", lambda name: {})
    # The longest first: 'SP33DY94-MIRCREW' before 'MIRCREW'
    assert SearchTags.detect_releaser("Film.2024.1080p.x264 Sp33dy94-MIRCrew.mkv") == "-Sp33dy94-MIRCrew"
    assert SearchTags.detect_releaser("Film.2024.1080p.x264.[LFi].mkv") == "-LFi"
    # Only at the end of the name, after a separator
    assert SearchTags.detect_releaser("Film.2024.1080p.x264.mkv") == ""
    assert SearchTags.detect_releaser("Film.2024.1080p.FooLFi.mkv") == ""


def video_manager(tag=None):
    from ittup.core.media_manager.VideoManager import VideoManager
    return VideoManager(contents=[], cli=argparse.Namespace(tag=tag))


def test_tag_comes_before_releaser_sign(monkeypatch):
    from ittup.core import config_settings
    monkeypatch.setattr(config_settings.user_preferences, "RELEASER_SIGN", "-MySign")
    assert video_manager("NAHOM").releaser_sign() == "-NAHOM"
    assert video_manager("-Dr4gon MIRCrew").releaser_sign() == "-Dr4gon MIRCrew"
    assert video_manager().releaser_sign() == "-MySign"
    monkeypatch.setattr(config_settings.user_preferences, "RELEASER_SIGN", "")
    # Read from the file name
    assert video_manager().releaser_sign() == ""


def test_tag_flag(monkeypatch):
    from ittup.common.command import CommandLine
    monkeypatch.setattr(sys, "argv", ["ittup", "-u", "/tmp/movie.mkv", "-tag", "NAHOM"])
    assert CommandLine().args.tag == "NAHOM"


def test_the_lists_are_no_longer_created():
    settings.Load.load_config()
    assert settings.DEFAULT_JSON_PATH.exists()
    assert [path for path in settings.OBSOLETE_LIST_FILES if path.exists()] == []


def test_the_lists_of_unit3dup_are_not_copied(tmp_path, monkeypatch):
    legacy, new = tmp_path / "Unit3Dup_config", tmp_path / "ittup_config"
    legacy.mkdir()
    for name in ("Unit3Dbot.json", "tags_list.json", "sign_list.json", "ban_list.json"):
        (legacy / name).write_text("{}")
    monkeypatch.setattr(settings, "CONFIG_DIR", new)
    monkeypatch.setattr(settings, "LEGACY_CONFIG_DIR", legacy)
    monkeypatch.setattr(settings, "LEGACY_CONFIG_FILES",
                        {name: new / path.name for name, path in settings.LEGACY_CONFIG_FILES.items()})
    settings.Load.migrate_legacy_config()
    assert sorted(path.name for path in new.iterdir()) == ["ittup.json"]
