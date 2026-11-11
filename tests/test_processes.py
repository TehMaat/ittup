# -*- coding: utf-8 -*-
import json
import os
import signal
import subprocess
import sys

import pytest

from ittup.common import processes
from ittup.common.processes import RunFile, running

# A process that registers in the folder of the test, says 'ready' and waits for a line on stdin
REGISTERED = """
import signal, sys
from pathlib import Path
from ittup.common.processes import register, working_on
signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(128 + signum))
register(sys.argv[2], item="Movie.mkv", folder=Path(sys.argv[1]))
working_on(sys.argv[3] if len(sys.argv) > 3 else None)
print("ready", flush=True)
sys.stdin.readline()
"""


def start(folder, mode="watcher", *args):
    process = subprocess.Popen([sys.executable, "-c", REGISTERED, str(folder), mode, *args],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    assert process.stdout.readline().strip() == "ready"
    return process


def test_a_running_process_is_listed_and_removed_when_it_ends(tmp_path):
    process = start(tmp_path, "watcher", "Show.S01E01.mkv")
    try:
        [found] = running(tmp_path)
        assert (found.pid, found.mode, found.item) == (process.pid, "watcher", "Show.S01E01.mkv")
        assert found.argv[1:] == [str(tmp_path), "watcher", "Show.S01E01.mkv"]
        assert f"PID {process.pid}" in found.describe() and "working on: Show.S01E01.mkv" in found.describe()
    finally:
        process.communicate("\n", timeout=10)
    assert process.returncode == 0
    assert running(tmp_path) == []
    assert list(tmp_path.iterdir()) == []


@pytest.mark.skipif(sys.platform == "win32", reason="SIGTERM is not a signal a process can handle on Windows")
def test_a_sigterm_removes_the_run_file(tmp_path):
    process = start(tmp_path, "scan")
    assert [found.mode for found in running(tmp_path)] == ["scan"]
    process.send_signal(signal.SIGTERM)
    process.communicate(timeout=10)
    assert process.returncode == 128 + signal.SIGTERM
    assert list(tmp_path.iterdir()) == []


@pytest.mark.skipif(sys.platform == "win32", reason="no SIGKILL on Windows")
def test_the_run_file_of_a_killed_process_is_stale_and_removed(tmp_path):
    process = start(tmp_path, "upload")
    process.kill()
    process.communicate(timeout=10)
    # Its files are still there, nobody holds the lock
    assert len(list(tmp_path.iterdir())) == 2
    assert running(tmp_path) == []
    assert list(tmp_path.iterdir()) == []


def test_a_stale_lock_is_removed(tmp_path):
    # Left by a process that ended without removing it: the PID may belong to another program now
    (tmp_path / f"{os.getppid()}.lock").write_text("")
    (tmp_path / f"{os.getppid()}.json").write_text(json.dumps({"pid": os.getppid(), "mode": "watcher"}))
    (tmp_path / "notes.lock").write_text("")
    assert running(tmp_path) == []
    assert [path.name for path in tmp_path.iterdir()] == ["notes.lock"]


def test_this_process_is_not_listed(tmp_path):
    with RunFile("upload", item="Movie.mkv", folder=tmp_path) as run_file:
        assert running(tmp_path) == []
        processes.working_on("Other.mkv")
        assert json.loads(run_file.info_path.read_text())["item"] == "Other.mkv"
    assert list(tmp_path.iterdir()) == []


def test_the_run_file_is_removed_after_an_exception(tmp_path):
    with pytest.raises(ValueError):
        with RunFile("scan", folder=tmp_path):
            assert len(list(tmp_path.iterdir())) == 2
            raise ValueError("crash")
    assert list(tmp_path.iterdir()) == []
    # Not registered any more
    processes.working_on("Movie.mkv")


def test_a_run_folder_that_cant_be_written_is_not_an_error(tmp_path):
    not_a_folder = tmp_path / "file"
    not_a_folder.write_text("")
    with RunFile("upload", folder=not_a_folder / "run"):
        processes.working_on("Movie.mkv")
    assert running(not_a_folder / "run") == []
