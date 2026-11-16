# -*- coding: utf-8 -*-
import os
import argparse

from ittup.common.utility import System
from ittup.common.about import APP_DESCRIPTION, APP_NAME, PACKAGE_NAME
from ittup.common.trackers import TRACKER_NAME, tracker_list


class RemovedFlag(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        parser.error(f"'{option_string}' has been removed: {APP_NAME} uploads only to ItaTorrents")


def tracker_resolution(value: str) -> str:
    """
    -fres: a resolution of the tracker, case-insensitive ('720P' -> '720p', 'Altro' -> 'altro')
    """
    resolutions = list(tracker_list[TRACKER_NAME]["RESOLUTION"])
    resolution = value.strip().lower()
    if resolution not in resolutions:
        raise argparse.ArgumentTypeError(f"invalid resolution '{value}', choose one of: {', '.join(resolutions)}")
    return resolution


class CommandLine:
    """
    Handle command line arguments
    """

    def __init__(self):

        # /////////////////////////
        # Main parser
        # /////////////////////////
        parser = argparse.ArgumentParser(
            prog=PACKAGE_NAME,
            description=f"{APP_DESCRIPTION}: manage torrents, uploads, searches and config checks",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )

        # /////////////////////////
        # Groups
        # /////////////////////////
        cfg_group = parser.add_argument_group("Config Commands")
        upload_group = parser.add_argument_group("Upload Commands")
        search_group = parser.add_argument_group("Search Commands")
        filter_group = parser.add_argument_group("Filter Options")
        special_group = parser.add_argument_group("Special Flags")

        # /////////////////////////
        # Config Commands
        # /////////////////////////
        cfg_group.add_argument(
            "-check", "--check",
            action="store_true",
            help="Check config files"
        )

        # /////////////////////////
        # Upload Commands
        # /////////////////////////
        upload_group.add_argument("-u", "--upload", type=str, help="Upload path")
        upload_group.add_argument("-f", "--folder", type=str, help="Upload folder")
        upload_group.add_argument("-scan", "--scan", type=str, help="Scan folder")
        upload_group.add_argument("-reseed", "--reseed", action="store_true", help="Reseed folder")
        upload_group.add_argument("-watcher", "--watcher", action="store_true", help="Start watcher")
        upload_group.add_argument("-notitle", "--notitle", type=str, help="Manual title")

        upload_group.add_argument(
            "-force",
            nargs='?',
            const="movie",
            type=str,
            default=None,
            help="Force category"
        )

        upload_group.add_argument("-noseed", "--noseed", action="store_true", help="Disable seeding")
        upload_group.add_argument("-noup", "--noup", action="store_true", help="Torrent only")
        upload_group.add_argument("-dup", "--duplicate", action="store_true", help="Check duplicates")
        upload_group.add_argument("-personal", "--personal", action="store_true", help="Personal release")
        upload_group.add_argument("-int", "--internal", action="store_true", help="Upload as internal release")
        upload_group.add_argument("-mod", "--moderation", action="store_true",
                                  help="Ask the tracker to moderate the upload")
        upload_group.add_argument("-ftp", "--ftp", action="store_true", help="Connect FTP")
        upload_group.add_argument("-fres", "--force-resolution", dest="force_resolution", type=tracker_resolution,
                                  help="Resolution of the upload instead of the one read from MediaInfo, for every"
                                       " file of the run (es. 720p, 480p, altro)")

        # Freeleech of the uploaded torrents
        freeleech_group = upload_group.add_mutually_exclusive_group()
        for percent in (25, 50, 75, 100):
            freeleech_group.add_argument(f"-fl{percent}", f"--freeleech{percent}", dest="freeleech",
                                         action="store_const", const=percent, help=f"Freeleech {percent}%%")

        # Removed flags: ITTup uploads only to ItaTorrents. Without this '-mt' would be parsed as '-m t'
        upload_group.add_argument("-mt", "--mt", "-tracker", "--tracker", nargs='?', action=RemovedFlag,
                                  help=argparse.SUPPRESS)

        # /////////////////////////
        # Search Commands
        # /////////////////////////
        search_group.add_argument("-dmp", "--dump", action="store_true", help="Dump titles")
        search_group.add_argument("-sch", "--search", type=str, help="Search torrent")
        search_group.add_argument("-db", "--dbsave", action="store_true", help="Save results")
        search_group.add_argument("-i", "--info", type=str, help="Torrent info")
        search_group.add_argument("-up", "--uploader", type=str, help="By uploader")
        search_group.add_argument("-d", "--description", type=str, help="By description")
        search_group.add_argument("-bd", "--bdinfo", type=str, help="Show BDInfo")
        search_group.add_argument("-m", "--mediainfo", type=str, help="Show MediaInfo")


        # /////////////////////////
        # Filter Options
        # /////////////////////////
        filter_group.add_argument("-st", "--startyear", type=str, help="Start year")
        filter_group.add_argument("-en", "--endyear", type=str, help="End year")
        filter_group.add_argument("-type", "--type", type=str, help="Type")
        filter_group.add_argument("-res", "--resolution", type=str, help="Resolution")
        filter_group.add_argument("-file", "--filename", type=str, help="Filename")
        filter_group.add_argument("-se", "--season", type=str, help="Season")
        filter_group.add_argument("-ep", "--episode", type=str, help="Episode")

        # IDs
        filter_group.add_argument("-tmdb", "--tmdb_id", type=str, help="TMDB ID")
        filter_group.add_argument("-imdb", "--imdb_id", type=str, help="IMDB ID")
        filter_group.add_argument("-tvdb", "--tvdb_id", type=int, help="TVDB ID")
        filter_group.add_argument("-mal", "--mal_id", type=str, help="MAL ID")
        filter_group.add_argument("-playid", "--playlist_id", type=str, help="Playlist ID")
        filter_group.add_argument("-coll", "--collection_id", type=str, help="Collection ID")

        # Status
        filter_group.add_argument("-free", "--freelech", type=str, help="Freeleech")
        filter_group.add_argument("-al", "--alive", action="store_true", help="Alive")
        filter_group.add_argument("-dd", "--dead", action="store_true", help="Dead")
        filter_group.add_argument("-dy", "--dying", action="store_true", help="Dying")

        # /////////////////////////
        # Special Flags
        # /////////////////////////
        special_group.add_argument("-du", "--doubleup", action="store_true", help="DoubleUp")
        special_group.add_argument("-fe", "--featured", action="store_true", help="Featured")
        special_group.add_argument("-re", "--refundable", action="store_true", help="Refundable")
        special_group.add_argument("-str", "--stream", action="store_true", help="Stream")
        special_group.add_argument("-sd", "--standard", action="store_true", help="SD")
        special_group.add_argument("-hs", "--highspeed", action="store_true", help="Highspeed")
        special_group.add_argument("-inter", "--intern_r", action="store_true", help="Internal releases")
        special_group.add_argument("-pr", "--prelease", action="store_true", help="Personal")
        special_group.add_argument(
            "-upgrade", "--upgrade",
            nargs="?",
            const="ask",
            choices=["ask", "wait", "stop", "force", "check"],
            help="Upgrade ITTup. With other ITTup processes running: ask, wait for them, stop them, force the upgrade."
                 " 'check' only checks for a new version"
        )

        # /////////////////////////
        # Parse args
        # /////////////////////////
        self.args = parser.parse_args()

        # /////////////////////////
        # Check scan path
        # /////////////////////////
        self.is_dir = os.path.isdir(self.args.scan) if self.args.scan else None

        # /////////////////////////
        # Expand upload path
        # /////////////////////////
        if self.args.upload:
            self.args.upload = os.path.expanduser(self.args.upload)

        # /////////////////////////
        # Validate force category
        # /////////////////////////
        if self.args.force:

            self.args.force = self.args.force[:10]

            valid_categories = [
                System.category_list[System.MOVIE],
                System.category_list[System.GAME],
                System.category_list[System.TV_SHOW],
                System.category_list[System.DOCUMENTARY]
            ]

            if self.args.force.lower() not in valid_categories:
                self.args.force = None
                print("Invalid -force category")
                exit()