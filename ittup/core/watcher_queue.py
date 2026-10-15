# -*- coding: utf-8 -*-
import json
import os
import shutil
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path

from ittup.view import custom_console

# Wait before the first retry, doubled at each one up to RETRY_MAX_DELAY
RETRY_BASE_DELAY = 60
RETRY_MAX_DELAY = 60 * 60


@dataclass
class QueueEntry:
    # The file or the folder moved to the watcher destination
    path: str
    # Failed attempts
    attempts: int = 0
    # Time (epoch) of the next attempt
    next_attempt: float = 0.0
    last_error: str = ""


@dataclass
class RunOutcome:
    """
    How the upload of a watcher entry ended: 'done', 'retry' (a temporary error) or 'failed'
    """
    status: str
    reason: str = ""
    # Torrent files created in the archive and never uploaded
    pending_torrents: list[str] = field(default_factory=list)


class UploadQueue:
    """
    The watcher uploads left to do, saved in a json file: after a crash or a restart the watcher goes on with them.
    An upload stopped by a temporary error (network, rate limit, tracker offline) is retried with an exponential
    backoff
    """

    def __init__(self, file: str | Path):
        self.file = Path(file)
        self.entries: list[QueueEntry] = self._load()

    def _load(self) -> list[QueueEntry]:
        try:
            with open(self.file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            return []
        except (OSError, ValueError) as e:
            custom_console.bot_error_log(f"Can't read the watcher queue '{self.file}': {e}. Starting a new one")
            return []

        entries = []
        for item in data if isinstance(data, list) else []:
            try:
                entry = QueueEntry(**item)
            except TypeError:
                continue
            # Moved or deleted by the user in the meantime
            if not os.path.exists(entry.path):
                custom_console.bot_warning_log(f"'{entry.path}' is no longer there: removed from the watcher queue")
                continue
            entries.append(entry)
        return entries

    def save(self) -> None:
        """
        Write the queue: a temporary file replaces the old one, so a crash never leaves half a file
        """
        self.file.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.file.with_name(self.file.name + ".tmp")
        with open(temporary, "w", encoding="utf-8") as f:
            json.dump([asdict(entry) for entry in self.entries], f, ensure_ascii=False, indent=4)
        os.replace(temporary, self.file)

    def __len__(self) -> int:
        return len(self.entries)

    def add(self, path: str) -> None:
        """ A new entry to upload, saved at once """
        if any(entry.path == path for entry in self.entries):
            return
        self.entries.append(QueueEntry(path=path))
        self.save()

    def remove(self, entry: QueueEntry) -> None:
        self.entries = [item for item in self.entries if item.path != entry.path]
        self.save()

    def due(self, now: float | None = None) -> list[QueueEntry]:
        """ The entries whose next attempt is due, in the order they were added """
        now = time.time() if now is None else now
        return [entry for entry in self.entries if entry.next_attempt <= now]

    @staticmethod
    def backoff(attempts: int) -> int:
        """ Seconds before the next attempt: 60, 120, 240.. up to an hour """
        return min(RETRY_BASE_DELAY * 2 ** max(attempts - 1, 0), RETRY_MAX_DELAY)

    def retry(self, entry: QueueEntry, reason: str, now: float | None = None) -> int:
        """
        Schedule the next attempt of an entry after a temporary error. Returns the seconds to wait
        """
        now = time.time() if now is None else now
        entry.attempts += 1
        entry.last_error = reason
        delay = self.backoff(entry.attempts)
        entry.next_attempt = now + delay
        self.save()
        return delay


def quarantine(path: str, quarantine_path: str, reasons: list[str], attempts: int) -> str | None:
    """
    Move a failed entry to the quarantine folder, with a '<name>.error.txt' file that tells why

    Returns:
        the new path, None if it can't be moved
    """
    name = os.path.basename(os.path.normpath(path))
    destination = Path(quarantine_path)
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / name
    # The same name failed before: keep both
    if target.exists():
        stem, ext = os.path.splitext(name) if os.path.isfile(path) else (name, "")
        target = destination / f"{stem}.{datetime.now():%Y%m%d-%H%M%S}{ext}"
    try:
        shutil.move(path, target)
    except OSError as e:
        custom_console.bot_error_log(f"Can't move '{path}' to the quarantine: {e}")
        return None

    report = [f"Date: {datetime.now():%Y-%m-%d %H:%M:%S}",
              f"Path: {path}",
              f"Attempts: {attempts}",
              "Reason:"] + [f"- {reason}" for reason in reasons or ["unknown"]]
    try:
        with open(f"{target}.error.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(report) + "\n")
    except OSError as e:
        custom_console.bot_error_log(f"Can't write the reason of the quarantine: {e}")
    return str(target)
