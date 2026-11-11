# -*- coding: utf-8 -*-
import importlib
import os
import shlex
import signal
import subprocess
import sys
import time
from pathlib import Path

from ittup.common.about import APP_NAME, PACKAGE_NAME, __version__
from ittup.common.processes import RUN_DIR, RunningProcess, running
from ittup.common.update_check import (UPGRADE_DOCS_URL, installed_version, is_newer, latest_version,
                                       parse_version, release_url)

# What to do with the ITTup processes that are running: 'ask' asks the user, 'check' only checks the version
ACTIONS = ("ask", "wait", "stop", "force", "check")
# Seconds between two checks of the processes that are running
POLL = 5

# Exit codes: an update is available (with 'check'), PyPI didn't answer
UPDATE_AVAILABLE = 1
PYPI_OFFLINE = 2


def upgrade(action: str = "ask", current: str = __version__, run_dir: Path = RUN_DIR) -> int:
    """
    Upgrades ITTup with the pip of the interpreter that runs it. Before that, the other ITTup processes that
    are running (watcher, scan, reseed, upload) are listed: the upgrade waits for them, stops them, goes on
    anyway or is cancelled, as 'action' says or as the user answers

    Returns the exit code: 0 upgraded or already up to date, 1 cancelled or failed (with 'check': an update is
    available), 2 PyPI didn't answer
    """
    if parse_version(current) is None:
        print(f"{APP_NAME} {current} is a source checkout or a dev build: upgrade it with git or pip")
        return 1
    latest = latest_version()
    if latest is None:
        print("PyPI didn't answer: try again later")
        return PYPI_OFFLINE
    if not is_newer(latest, current):
        print(f"{APP_NAME} {current} is up to date")
        return 0
    print(f"{APP_NAME} {latest} is available (installed: {current}). What's new: {release_url(latest)}")
    if action == "check":
        return UPDATE_AVAILABLE

    others = running(run_dir)
    if others:
        print(f"\n⚠ {APP_NAME} processes running: {len(others)}")
        for process in others:
            print(f"  {process.describe()}")
        print("Upgrading now can stop an upload halfway.")
        if action == "ask":
            action = ask()
        if action == "stop" and sys.platform == "win32":
            print("On Windows the processes can't be stopped cleanly: close them, or wait for them")
            return 1
        try:
            if action == "wait":
                print("Waiting for them to end (Ctrl-c to cancel)..")
                wait(others, run_dir)
            elif action == "stop":
                if not stop(others, run_dir):
                    print("Upgrade cancelled")
                    return 1
            elif action != "force":
                print("Upgrade cancelled")
                return 1
        except KeyboardInterrupt:
            print("\nUpgrade cancelled")
            return 1

    command = [sys.executable, "-m", "pip", "install", "--upgrade", f"{PACKAGE_NAME}=={latest}"]
    print(f"\n{shlex.join(command)}")
    try:
        result = subprocess.run(command, check=False)
    except OSError as e:
        print(f"pip didn't start: {e}")
        return 1
    importlib.invalidate_caches()
    installed = installed_version()
    if result.returncode != 0 or installed != latest:
        print(f"\nThe upgrade failed (installed: {installed}). Upgrade by hand: {UPGRADE_DOCS_URL}")
        return 1

    print(f"\n{APP_NAME} {latest} installed. Run '{PACKAGE_NAME} -check': a new version can add new settings")
    if others:
        print(f"Restart the {APP_NAME} processes that were running:")
        for process in others:
            print(f"  {shlex.join(process.argv) if process.argv else f'PID {process.pid} ({process.mode})'}")
    return 0


def ask() -> str:
    """
    What to do with the processes that are running: wait, stop, force or cancel
    """
    if not sys.stdin.isatty():
        print(f"No terminal to ask what to do: use '{PACKAGE_NAME} --upgrade wait', 'stop' or 'force'")
        return "cancel"
    choices = {"w": "wait", "f": "force", "n": "cancel"}
    question = "[W]ait for them to end / [F]orce the upgrade / [N]o, cancel: "
    if sys.platform != "win32":
        choices["s"] = "stop"
        question = ("[W]ait for them to end / [S]top them and upgrade (a watcher ends its upload first) / "
                    "[F]orce the upgrade / [N]o, cancel: ")
    while True:
        try:
            answer = input(question).strip().lower()[:1]
        except (EOFError, KeyboardInterrupt):
            print()
            return "cancel"
        if answer in choices:
            return choices[answer]


def wait(processes: list[RunningProcess], run_dir: Path = RUN_DIR, poll: float = POLL) -> None:
    """
    Waits until the processes have ended
    """
    pids = {process.pid for process in processes}
    while pids & {process.pid for process in running(run_dir)}:
        time.sleep(poll)


def stop(processes: list[RunningProcess], run_dir: Path = RUN_DIR, poll: float = POLL) -> bool:
    """
    Sends a SIGTERM to the processes and waits until they have ended: a watcher ends its upload first,
    the other processes stop at once. False if a process can't be stopped (another user's)
    """
    all_stopped = True
    for process in processes:
        try:
            os.kill(process.pid, signal.SIGTERM)
            print(f"SIGTERM sent to PID {process.pid} ({process.mode})")
        except ProcessLookupError:
            # Already ended
            pass
        except OSError as e:
            print(f"PID {process.pid} can't be stopped: {e}")
            all_stopped = False
    if not all_stopped:
        return False
    print("Waiting for them to end (Ctrl-c to cancel)..")
    wait(processes, run_dir, poll=poll)
    return True
