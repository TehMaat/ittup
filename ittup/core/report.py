# -*- coding: utf-8 -*-
import json
import os

# Exit code of a run stopped by a temporary error (BSD EX_TEMPFAIL)
TEMPORARY_FAILURE = 75


class TemporaryFailure(SystemExit):
    """
    A network error, a timeout, a rate limit or a tracker error that may go away by itself.
    The bot exits like before (with code 75): the watcher retries the upload later instead of quarantining it
    """

    def __init__(self, reason: str):
        super().__init__(TEMPORARY_FAILURE)
        self.reason = reason


class UploadReport:
    """
    What happened to the contents processed in this process: the watcher reads it to retry or quarantine an entry

    The torrent files created and not uploaded yet are also written in a journal file, when it is set:
    the watcher reads it even when the upload was killed or the watcher crashed
    """

    def __init__(self):
        self.failures: list[str] = []
        self.pending_torrents: list[str] = []
        self.journal: str | None = None

    def reset(self, journal: str | None = None) -> None:
        self.failures = []
        self.pending_torrents = []
        self.journal = journal
        self._write_journal()

    def torrent_created(self, path: str) -> None:
        """ A torrent file in the archive, not uploaded yet """
        if path not in self.pending_torrents:
            self.pending_torrents.append(path)
            self._write_journal()

    def uploaded(self, path: str) -> None:
        if path in self.pending_torrents:
            self.pending_torrents.remove(path)
            self._write_journal()

    def failed(self, name: str, reason: str) -> None:
        self.failures.append(f"'{name}': {reason}")

    def _write_journal(self) -> None:
        if not self.journal:
            return
        try:
            with open(self.journal, "w", encoding="utf-8") as f:
                json.dump(self.pending_torrents, f)
        except OSError:
            pass

    @staticmethod
    def read_journal(journal: str) -> list[str]:
        try:
            with open(journal, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return []
        return [str(path) for path in data] if isinstance(data, list) else []

    @staticmethod
    def remove_torrents(paths: list[str]) -> None:
        """
        Delete the torrent files that were never uploaded: the watcher would take them for old uploads
        """
        for path in paths:
            try:
                os.remove(path)
            except OSError:
                pass


report = UploadReport()
