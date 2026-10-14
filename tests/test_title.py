# -*- coding: utf-8 -*-
import pytest

from ittup.common.utility import ManageTitles


@pytest.mark.parametrize("title, name, spelling", [
    ("Spider Man No Way Home", "Spider-Man.No.Way.Home.2021.1080p.WEB-DL.mkv", "Spider-Man No Way Home"),
    ("Mission Impossible Dead Reckoning", "Mission: Impossible - Dead Reckoning (2023) 1080p.mkv",
     "Mission: Impossible - Dead Reckoning"),
    ("Fast & Furious", "Fast & Furious 2009 1080p BluRay.mkv", "Fast & Furious"),
    ("Ciao! Come Stai", "Ciao! Come Stai 2020 1080p.mkv", "Ciao! Come Stai"),
    ("Il Ragazzo e l Airone", "Il.Ragazzo.e.l'Airone.2023.1080p.mkv", "Il Ragazzo e l'Airone"),
    ("Ocean s Eleven", "Ocean's_Eleven_2001_1080p.mkv", "Ocean's Eleven"),
    ("S W A T", "S.W.A.T.2017.S01.1080p", "S.W.A.T"),
    ("Mr Robot", "Mr. Robot S01 1080p", "Mr. Robot"),
    # Not in the name: the guessit title
    ("Some Title", "Other.Name.2020.mkv", "Some Title"),
    (None, "Other.Name.2020.mkv", None),
])
def test_original_spelling(title, name, spelling):
    assert ManageTitles.original_spelling(title, name) == spelling
