# -*- coding: utf-8 -*-
import atexit
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import IO

from ittup.common.settings import CONFIG_DIR

# A file for each running watcher, scan, reseed or upload: '<pid>.lock' held locked while the process runs and
# '<pid>.json' with what it is doing. The OS releases the lock when the process ends, also on a crash or a kill:
# a lock nobody holds is stale, and a PID reused by another program is never mistaken for ITTup
RUN_DIR: Path = CONFIG_DIR / "run"

if sys.platform == "win32":
    import msvcrt

    # msvcrt locks a range of bytes: lock one far from the start, so the file can still be read
    _LOCK_OFFSET = 1 << 30

    def _lock(file: IO[str]) -> bool:
        file.seek(_LOCK_OFFSET)
        try:
            msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            return False
        return True
else:
    import fcntl

    def _lock(file: IO[str]) -> bool:
        try:
            fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return False
        return True


@dataclass
class RunningProcess:
    """
    An ITTup process that is running: its PID, the mode (watcher, scan, reseed, upload..), when it started,
    the item it is working on and its command line
    """
    pid: int
    mode: str = "?"
    started: float = 0
    item: str | None = None
    argv: list[str] = field(default_factory=list)

    def describe(self) -> str:
        started = datetime.fromtimestamp(self.started).strftime("%Y-%m-%d %H:%M") if self.started else "?"
        text = f"PID {self.pid:<7} {self.mode:<8}  started {started}"
        return f"{text}   working on: {self.item}" if self.item else text


class RunFile:
    """
    Registers the current process while it runs (a context manager): the lock file and the info file are
    removed at the end, also after an exception or a SIGTERM turned into SystemExit
    """

    def __init__(self, mode: str, item: str | None = None, folder: Path = RUN_DIR):
        self.folder = Path(folder)
        self.info = RunningProcess(pid=os.getpid(), mode=mode, started=time.time(), item=item,
                                   argv=[os.path.basename(sys.argv[0]), *sys.argv[1:]])
        self.lock_path = self.folder / f"{self.info.pid}.lock"
        self.info_path = self.folder / f"{self.info.pid}.json"
        self._lock_file: IO[str] | None = None

    def __enter__(self) -> "RunFile":
        global _current
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
            self._lock_file = open(self.lock_path, "a+")
            if not _lock(self._lock_file):
                self._lock_file.close()
                self._lock_file = None
                return self
            self._write()
        except OSError:
            # Not registered: the bot still runs, only the other ITTup processes won't see it
            self._lock_file = None
            return self
        _current = self
        return self

    def __exit__(self, *exc_info: object) -> None:
        global _current
        if _current is self:
            _current = None
        if self._lock_file is None:
            return
        # The info file first: a lock file alone is a process starting or one that ended
        _remove(self.info_path)
        self._lock_file.close()
        self._lock_file = None
        _remove(self.lock_path)

    def working_on(self, item: str | None) -> None:
        if self._lock_file is not None:
            self.info.item = item
            self._write()

    def _write(self) -> None:
        temporary = self.info_path.with_suffix(".tmp")
        try:
            temporary.write_text(json.dumps(self.info.__dict__), encoding="utf-8")
            os.replace(temporary, self.info_path)
        except OSError:
            pass


# The RunFile of this process, if it is registered
_current: RunFile | None = None


def register(mode: str, item: str | None = None, folder: Path = RUN_DIR) -> RunFile:
    """
    Registers this process until it exits
    """
    run_file = RunFile(mode, item=item, folder=folder).__enter__()
    atexit.register(run_file.__exit__)
    return run_file


def working_on(item: str | None) -> None:
    """
    Tells the other ITTup processes what this process is working on. Nothing if it isn't registered
    """
    if _current is not None:
        _current.working_on(item)


def running(folder: Path = RUN_DIR) -> list[RunningProcess]:
    """
    The other ITTup processes that are running. The files of the processes that ended are removed
    """
    processes: list[RunningProcess] = []
    try:
        lock_paths = sorted(Path(folder).glob("*.lock"))
    except OSError:
        return processes
    for lock_path in lock_paths:
        try:
            pid = int(lock_path.stem)
        except ValueError:
            continue
        if pid == os.getpid():
            continue
        info_path = lock_path.with_suffix(".json")
        try:
            with open(lock_path, "a+") as lock_file:
                stale = _lock(lock_file)
        except OSError:
            continue
        if stale:
            _remove(info_path)
            _remove(lock_path)
            continue
        try:
            info = json.loads(info_path.read_text(encoding="utf-8"))
            processes.append(RunningProcess(**{**info, "pid": pid}))
        except (OSError, ValueError, TypeError):
            # Still starting: only its PID is known
            processes.append(RunningProcess(pid=pid))
    return processes


def _remove(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass
