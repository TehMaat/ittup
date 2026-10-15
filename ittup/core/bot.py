# -*- coding: utf-8 -*-

from pathlib import Path
import argparse
import multiprocessing
import os
import math
import signal
import sys
import time
import shutil
import traceback

import httpx
import requests

from ittup.core.media import Media
from ittup.core.media_manager.ContentManager import ContentManager
from ittup.core.media_manager.TorrentManager import TorrentManager
from ittup.core.report import report, TemporaryFailure, TEMPORARY_FAILURE
from ittup.core.watcher_queue import UploadQueue, QueueEntry, RunOutcome, quarantine

from ittup.common.external_services.ftpx.core.models.list import FTPDirectory
from ittup.common.external_services.ftpx.core.menu import Menu
from ittup.common.external_services.ftpx.client import Client
from ittup.common.extractor import Extractor
from ittup.common.utility import System

from ittup.view import custom_console


class Bot:
    """
    A Bot class that manages media files, including processing, torrent management,TMDB ,FTP

    Methods:
        run(): Starts the media processing and torrent handling tasks
        watcher(duration: int, watcher_path: str): Monitors a folder for changes and processes files
        ftp(): Connects to a remote FTP server and processes files
    """

    # Bot Manager
    def __init__(self, path: str, cli: argparse.Namespace, trackers_name_list: list, tags_list = None, mode="man",
                 torrent_archive_path = None, sign_list= None, ban_list= None):
        """
        Initializes the Bot instance with path, command-line interface object, and mode

        Args:
            path (str): The path to the directory or file to be managed
            cli (argparse.Namespace): The command-line arguments object
            mode (str): The mode of operation, default is 'man'
        """
        self.trackers_name_list = trackers_name_list
        self.torrent_archive_path = torrent_archive_path
        self.content_manager = None
        self.tags_list: dict = tags_list
        self.sign_list: dict = sign_list
        self.ban_list: dict = ban_list
        self.path = path.strip()
        self.cli = cli
        self.mode = mode


    def contents(self, include_paths: list[str] | None = None) -> bool | list[Media]:
        """
        Start the process of analyzing and processing media files
        This method retrieves media files

        Args:
            include_paths: if set, only the media with these paths are processed
        """
        custom_console.panel_message("Analyzing your media files... Please wait")

        # Check permission
        try:
            os.stat(self.path)
        except PermissionError:
            custom_console.bot_error_log(f"Permission denied: {self.path}")
            return False
        except FileNotFoundError:
            custom_console.bot_error_log(f"Path not found: {self.path}")
            return False

        # Get a Files list with basic attributes and create a content object for each
        self.content_manager: ContentManager = ContentManager(path=self.path, mode=self.mode, cli=self.cli,
                                                              include_paths=include_paths)
        contents = self.content_manager.process()

        # -u requires a single file
        if not contents:
            custom_console.bot_error_log("There are no Media to process")
            return False

        # Print the list of files being processed
        custom_console.bot_process_table_log(contents)

        return contents


    def run(self, include_paths: list[str] | None = None) -> bool:
        """
        processes the files using the TorrentManager and SeedManager

        Args:
            include_paths: if set, only the media with these paths are processed
        """

        # Get the user content
        contents = self.contents(include_paths=include_paths)
        if not contents:
            # Discarded: the watcher moves it to the quarantine
            for path in include_paths or []:
                report.failed(os.path.basename(path), "no media to upload: no video file or an unsupported type")
            return False

        # Instance a new run
        torrent_manager = TorrentManager(cli=self.cli, tracker_archive=self.torrent_archive_path,
                                         tags_list=self.tags_list, sign_list=self.sign_list, ban_list=self.ban_list)
        # Process the torrents content (files)
        torrent_manager.process(contents=contents)

        # We want to reseed
        if self.cli.reseed:
            torrent_manager.reseed(trackers_name_list=self.trackers_name_list)
        else:
            # otherwise run the torrents creations and the upload process
            torrent_manager.run(trackers_name_list=self.trackers_name_list)
        return True


    def watcher(self, duration: int, watcher_path: str, destination_path: str, timeout: int = 0,
                quarantine_path: str | None = None, max_retries: int = 5, queue_file: str | None = None) -> bool:
        """
        Monitors the watcher path for new files, moves them to the destination folder,
        then uploads them to the tracker

        Each cycle takes a snapshot of the watcher folder, waits 'duration' seconds and takes a second one.
        Only the entries whose size did not change between the two snapshots are moved (a file still
        being copied is left for the next cycle) and only the moved entries are processed

        Every moved entry goes into a persistent queue (queue_file) before its upload: after a crash or a restart
        the watcher goes on with the uploads left. An upload stopped by a temporary error (network, rate limit,
        tracker offline, timeout) is retried with an exponential backoff, up to 'max_retries' times.
        An upload that fails for good, or that runs out of retries, is moved to 'quarantine_path' with a file
        that tells why, instead of being retried forever

        The waiting message is logged once when the watcher becomes idle, not on every cycle,
        so an idle watcher doesn't fill the log
        Each moved entry is processed in its own child process: if it crashes or is still running after
        'timeout' seconds, it is stopped and the watcher goes on with the next entry

        Args:
            duration (int): The time duration in seconds for the watchdog to wait before checking again
            watcher_path (str): The path to the folder being monitored for new files
            destination_path: The destination path for the new files
            timeout (int): Maximum seconds for processing a single entry. 0 = no limit
            quarantine_path: where the failed entries are moved. None = they stay in the destination folder
            max_retries: retries of an upload stopped by a temporary error
            queue_file: the json file of the queue. None = a queue file in the destination folder
        """
        self.path = str(destination_path)
        watcher_path = Path(watcher_path)
        destination = Path(destination_path)
        queue = UploadQueue(queue_file or destination / ".ittup_watcher_queue.json")
        # The torrent files of the running upload not uploaded yet
        journal = str(queue.file.with_suffix(".pending.json"))
        # The watcher stopped during an upload: its torrent files were never uploaded
        report.remove_torrents(report.read_journal(journal))
        report.reset(journal=journal)
        report.journal = None
        # Log the waiting message only when the watcher becomes idle
        announce_idle = True
        try:
            # Go on with the uploads left by the last run
            if queue.due():
                custom_console.bot_log(f"WATCHDOG: {len(queue)} uploads left in the queue by the last run")
                self._process_queue(queue, timeout=timeout, quarantine_path=quarantine_path,
                                    max_retries=max_retries, journal=journal)

            # Watchdog loop
            while True:
                # Return if the watcher path doesn't exist
                if not watcher_path.exists():
                    custom_console.bot_error_log("Watcher path does not exist or is not configured\n")
                    return False

                # First check
                previous_snapshot = self._snapshot(watcher_path)

                if announce_idle:
                    if not previous_snapshot:
                        custom_console.bot_log("There are no files in the Watcher folder")
                    if len(queue):
                        custom_console.bot_log(f"WATCHDOG: {len(queue)} uploads waiting to be retried")
                    custom_console.bot_log(f"WATCHDOG: checking the Watcher folder every {duration} seconds."
                                           f" Ctrl-c to Exit")
                    announce_idle = False

                custom_console.bot_countdown(duration)

                # Second check
                current_snapshot = self._snapshot(watcher_path)

                # Move only the entries whose size is unchanged since the previous check
                # Alphanumeric order: the entries are uploaded in the same order
                for name, signature in sorted(current_snapshot.items(), key=lambda item: System.natural_key(item[0])):
                    src = watcher_path / name
                    if previous_snapshot.get(name) != signature:
                        custom_console.bot_log(f"'{name}' is still being copied. Wait for the next cycle")
                        continue

                    dest = destination / name
                    # Limit the length of file paths printed
                    limiter_src = '...' if len(str(src)) > 50 else ''
                    limiter_dest = '...' if len(str(dest)) > 50 else ''
                    custom_console.bot_log(
                        f"{str(src)[:50]}{limiter_src} -> from 'watch folder' to 'destination folder'"
                        f" -> {str(dest)[:50]}{limiter_dest}"
                    )
                    try:
                        self._move(src, dest)
                    except OSError as e:
                        custom_console.bot_error_log(e)
                        continue
                    # Saved in the queue at once: a crash before the upload doesn't lose it
                    queue.add(os.path.normpath(dest))

                # Start uploading the new files and the retries that are due, one at a time
                if not queue.due():
                    continue
                print()
                self._process_queue(queue, timeout=timeout, quarantine_path=quarantine_path, max_retries=max_retries,
                                    journal=journal)
                print()
                announce_idle = True

        except KeyboardInterrupt:
            custom_console.bot_log("Exiting...")
        return True

    def _process_queue(self, queue: UploadQueue, timeout: int, quarantine_path: str | None,
                       max_retries: int, journal: str | None = None) -> None:
        """
        Upload the entries of the queue that are due: retry the temporary errors, quarantine the failures
        """
        for entry in queue.due():
            name = os.path.basename(entry.path)
            if not os.path.exists(entry.path):
                custom_console.bot_warning_log(f"'{entry.path}' is no longer there: removed from the watcher queue")
                queue.remove(entry)
                continue
            if entry.attempts:
                custom_console.bot_log(f"WATCHDOG: retry {entry.attempts}/{max_retries} of '{name}'")

            outcome = self._run_isolated(include_path=entry.path, timeout=timeout, journal=journal)

            if outcome.status != "done":
                # The torrent files never uploaded: left in the archive the next attempt would skip them
                # as old uploads
                report.remove_torrents(outcome.pending_torrents)

            if outcome.status == "done":
                queue.remove(entry)
            elif outcome.status == "retry" and entry.attempts < max_retries:
                delay = queue.retry(entry, outcome.reason)
                custom_console.bot_warning_log(
                    f"'{name}': {outcome.reason}. Retry {entry.attempts}/{max_retries} in {delay} seconds\n")
            else:
                reasons = [outcome.reason]
                if outcome.status == "retry":
                    reasons.append(f"still failing after {max_retries} retries")
                self._quarantine(entry, reasons=reasons, quarantine_path=quarantine_path)
                queue.remove(entry)

    @staticmethod
    def _quarantine(entry: QueueEntry, reasons: list[str], quarantine_path: str | None) -> None:
        """
        Move a failed entry to the quarantine with the reason of the failure
        """
        name = os.path.basename(entry.path)
        if not quarantine_path:
            custom_console.bot_error_log(f"'{name}' failed: {'; '.join(reasons)}\n")
            return
        new_path = quarantine(entry.path, quarantine_path=quarantine_path, reasons=reasons,
                              attempts=entry.attempts + 1)
        if new_path:
            custom_console.bot_error_log(f"'{name}' failed and was moved to the quarantine '{new_path}':"
                                         f" {'; '.join(reasons)}\n")

    def _run_isolated(self, include_path: str, timeout: int, journal: str | None = None) -> RunOutcome:
        """
        Processes a single entry in a child process, so that a file which hangs or crashes the upload
        doesn't stop the watcher. The child is stopped if it is still running after 'timeout' seconds

        Args:
            journal: the file where the run writes the torrent files not uploaded yet

        Returns:
            how the upload ended: done, retry (a temporary error) or failed, and the torrent files never uploaded
        """
        report.reset(journal=journal)
        custom_console.recent_errors.clear()
        try:
            outcome = self._run_entry_isolated(include_path=include_path, timeout=timeout)
            outcome.pending_torrents = report.read_journal(journal) if journal else list(report.pending_torrents)
            return outcome
        finally:
            report.reset(journal=journal)
            report.journal = None

    def _run_entry_isolated(self, include_path: str, timeout: int) -> RunOutcome:
        """
        Runs the upload of an entry in a child process (or in the watcher where fork is not available)
        """

        # The child must be a fork of the watcher: it shares the loaded config and the console (the questions
        # are answered on stdin), and the Bot can't be pickled for 'spawn' or 'forkserver' (the default
        # since Python 3.14). Where fork isn't available or safe (Windows, macOS) the entry runs in the watcher
        if "fork" not in multiprocessing.get_all_start_methods() or sys.platform == "darwin":
            exitcode, reason = _run_entry(self, include_path)
            return run_outcome(exitcode, reason=reason, failures=report.failures,
                               errors=list(custom_console.recent_errors))

        name = os.path.basename(include_path)
        context = multiprocessing.get_context("fork")
        receiver, sender = context.Pipe(duplex=False)
        process = context.Process(target=_run_worker, args=(self, include_path, sender), daemon=True)
        process.start()
        sender.close()
        result = {}
        try:
            process.join(timeout if timeout > 0 else None)
            if process.is_alive():
                custom_console.bot_error_log(
                    f"'{name}' is stuck: still processing after {timeout} seconds. Skipped, restarting the watcher\n"
                )
                return RunOutcome("retry", f"still processing after {timeout} seconds")
            if receiver.poll():
                try:
                    result = receiver.recv()
                except (EOFError, OSError):
                    result = {}
        finally:
            receiver.close()
            # Stop the child if it timed out or if the user pressed Ctrl-c
            if process.is_alive():
                process.terminate()
                process.join(10)
                if process.is_alive():
                    process.kill()
                    process.join()

        if process.exitcode not in (0, TEMPORARY_FAILURE):
            custom_console.bot_error_log(
                f"'{name}' stopped with an error (exit code {process.exitcode}). Skipped, restarting the watcher\n"
            )
        return run_outcome(process.exitcode, reason=result.get("reason", ""), failures=result.get("failures", []),
                           errors=result.get("errors", []))

    @staticmethod
    def _snapshot(watcher_path: Path) -> dict[str, tuple]:
        """
        Returns a signature for each entry of the watcher folder: the file size or, for a folder,
        the relative path and size of each file it contains
        """
        snapshot = {}
        try:
            entries = list(watcher_path.iterdir())
        except OSError as e:
            custom_console.bot_error_log(e)
            return snapshot

        for entry in entries:
            try:
                if entry.is_dir():
                    snapshot[entry.name] = tuple(sorted(
                        (str(file.relative_to(entry)), file.stat().st_size)
                        for file in entry.rglob("*") if file.is_file()
                    ))
                else:
                    snapshot[entry.name] = (entry.stat().st_size,)
            except OSError:
                # The entry changed while we were reading it: wait for the next cycle
                continue
        return snapshot

    @staticmethod
    def _move(src: Path, dest: Path) -> None:
        """
        Moves a file or a folder to dest. A folder is merged into dest if it already exists
        """
        if src.is_dir() and dest.is_dir():
            for root, dirs, files in os.walk(src, topdown=False):
                dest_root = dest / Path(root).relative_to(src)
                dest_root.mkdir(parents=True, exist_ok=True)
                for file_name in files:
                    shutil.move(str(Path(root) / file_name), str(dest_root / file_name))
                # Remove the empty source directory
                os.rmdir(root)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))


    def ftp(self)-> None:
        """
        Connects to a remote FTP server and interacts with files.

        This method handles FTP connection, navigation, and file download from the remote server
        """
        custom_console.bot_question_log("\nConnecting to the remote FTP...\n")

        # FTP service
        ftp_client = Client()
        custom_console.bot_question_log(f"Connected to {ftp_client.sys_info()}\n\n")

        menu = Menu()

        page = ftp_client.home_page()
        menu.show(table=page)

        while True:
            user_option = ftp_client.user_input()
            page = ftp_client.input_manager(user_option)
            if page == 0:
                ftp_client.quit()
                break
            if not page:
                continue

            # Display selected folder or file
            if isinstance(page, FTPDirectory):
                ftp_directory_name = page.name
                if page.type == "Folder":
                    page = ftp_client.change_path(selected_folder=ftp_directory_name)
                    menu.show(table=page)
                else:
                    ftp_client.select_file(one_file_selected=page)
                continue

            # Show page as table
            menu.show(table=page)

        if ftp_client.download_to_local_path:
            self.path = os.path.dirname(ftp_client.download_to_local_path)
            self.mode = 'folder'
            # Upload -f process
            # Decompress .rar files if the flags are set
            extractor = Extractor(compressed_media__path=self.path)
            result = extractor.unrar()
            if result is False:
                custom_console.bot_error_log("Unrar Exit")
                exit(1)

            self.run()
        return None


def run_outcome(exitcode: int | None, reason: str, failures: list[str], errors: list[str]) -> RunOutcome:
    """
    How the upload of a watcher entry ended, from the exit code and the report of the run
    """
    if exitcode == TEMPORARY_FAILURE:
        status, reason = "retry", reason or (errors[-1] if errors else "temporary error")
    elif not exitcode:
        status, reason = ("failed", "; ".join(failures)) if failures else ("done", "")
    else:
        status = "failed"
        reason = (reason or "; ".join(failures) or (errors[-1] if errors else "")
                  or f"stopped with exit code {exitcode}")
    return RunOutcome(status, reason)


def _run_entry(bot: Bot, include_path: str) -> tuple[int, str]:
    """
    Upload a watcher entry. Returns the exit code (0, 75 for a temporary error) and the reason of a failure
    """
    try:
        bot.run(include_paths=[include_path])
    except TemporaryFailure as e:
        return TEMPORARY_FAILURE, e.reason
    except SystemExit as e:
        if isinstance(e.code, int) or e.code is None:
            return e.code or 0, ""
        return 1, str(e.code)
    except (requests.RequestException, httpx.HTTPError) as e:
        return TEMPORARY_FAILURE, f"network error: {e}"
    except Exception as e:
        traceback.print_exc()
        return 1, f"{type(e).__name__}: {e}"
    return 0, ""


def _run_worker(bot: Bot, include_path: str, sender) -> None:
    """
    Child process entry point for Bot._run_isolated: sends the report of the run to the watcher
    """
    # Turn SIGTERM into SystemExit: subprocess.run then kills the running ffmpeg/ffprobe before exiting
    signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(1))

    # multiprocessing redirects the child's stdin to devnull: reconnect it to the console,
    # so the questions (TMDB ID, duplicates..) can still be answered
    try:
        sys.stdin = open(0, closefd=False)
    except OSError:
        pass

    exitcode, reason = 1, ""
    try:
        exitcode, reason = _run_entry(bot, include_path)
    except KeyboardInterrupt:
        # Ctrl-c reaches the watcher too: let it print the exit message
        exitcode = 1
    finally:
        try:
            sender.send({"failures": [failure[:1000] for failure in report.failures], "reason": reason[:1000],
                         "errors": [error[:1000] for error in custom_console.recent_errors]})
        except (OSError, ValueError):
            pass
        sender.close()
    sys.exit(exitcode)
