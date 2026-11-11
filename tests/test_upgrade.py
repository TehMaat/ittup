# -*- coding: utf-8 -*-
import signal
import sys
from types import SimpleNamespace

import pytest

from ittup.common import upgrade as upgrade_module
from ittup.common.processes import RunningProcess
from ittup.common.upgrade import upgrade

WATCHER = RunningProcess(pid=12345, mode="watcher", started=0, item="Movie.mkv", argv=["ittup", "-watcher"])


@pytest.fixture
def pypi(monkeypatch):
    """
    PyPI has 'latest', no process is running and pip installs what it is asked for
    """
    state = SimpleNamespace(latest="1.13.0", installed="1.12.1", running=[[]], pip=[], pip_code=0, killed=[])

    def run(command, check=False):
        state.pip.append(command)
        if state.pip_code == 0:
            state.installed = command[-1].split("==")[1]
        return SimpleNamespace(returncode=state.pip_code)

    def running(run_dir):
        return state.running.pop(0) if len(state.running) > 1 else state.running[0]

    monkeypatch.setattr(upgrade_module, "latest_version", lambda: state.latest)
    monkeypatch.setattr(upgrade_module, "installed_version", lambda: state.installed)
    monkeypatch.setattr(upgrade_module, "running", running)
    monkeypatch.setattr(upgrade_module.subprocess, "run", run)
    monkeypatch.setattr(upgrade_module.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(upgrade_module.os, "kill", lambda pid, sig: state.killed.append((pid, sig)))
    return state


def test_no_update_available(pypi, capsys):
    pypi.latest = "1.12.1"
    assert upgrade(current="1.12.1") == 0
    assert pypi.pip == []
    assert "1.12.1 is up to date" in capsys.readouterr().out


def test_pypi_offline(pypi, capsys):
    pypi.latest = None
    assert upgrade(current="1.12.1") == 2
    assert pypi.pip == []
    assert "PyPI didn't answer" in capsys.readouterr().out


def test_a_source_checkout_is_not_upgraded(pypi):
    assert upgrade(current="0.0.0+unknown") == 1
    assert pypi.pip == []


def test_check_only(pypi, capsys):
    assert upgrade("check", current="1.12.1") == 1
    assert pypi.pip == []
    out = capsys.readouterr().out
    assert "1.13.0 is available (installed: 1.12.1)" in out and "/releases/tag/1.13.0" in out


def test_upgrade_without_processes_running(pypi, capsys):
    assert upgrade(current="1.12.1") == 0
    # The pip of the interpreter that runs ITTup, and exactly the version announced
    assert pypi.pip == [[sys.executable, "-m", "pip", "install", "--upgrade", "ittup==1.13.0"]]
    assert "ITTup 1.13.0 installed" in capsys.readouterr().out


def test_an_rc_installed_is_upgraded_to_the_release(pypi):
    assert upgrade(current="1.13.0rc2") == 0
    assert pypi.pip[0][-1] == "ittup==1.13.0"


def test_pip_fails(pypi, capsys):
    pypi.pip_code = 1
    assert upgrade(current="1.12.1") == 1
    assert "The upgrade failed (installed: 1.12.1)" in capsys.readouterr().out


def test_processes_running_and_no_terminal_to_ask(pypi, monkeypatch, capsys):
    pypi.running = [[WATCHER]]
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=lambda: False))
    assert upgrade(current="1.12.1") == 1
    assert pypi.pip == []
    out = capsys.readouterr().out
    assert "ITTup processes running: 1" in out and "PID 12345" in out and "working on: Movie.mkv" in out
    assert "Upgrade cancelled" in out


def test_force_with_processes_running(pypi, capsys):
    pypi.running = [[WATCHER]]
    assert upgrade("force", current="1.12.1") == 0
    assert len(pypi.pip) == 1 and pypi.killed == []
    out = capsys.readouterr().out
    assert "Restart the ITTup processes that were running" in out and "  ittup -watcher" in out


def test_wait_for_the_processes(pypi):
    # Still running at the first check, ended at the second one
    pypi.running = [[WATCHER], [WATCHER], []]
    assert upgrade("wait", current="1.12.1") == 0
    assert pypi.running == [[]] and len(pypi.pip) == 1


def test_wait_cancelled_with_ctrl_c(pypi, monkeypatch):
    pypi.running = [[WATCHER]]

    def interrupt(seconds):
        raise KeyboardInterrupt
    monkeypatch.setattr(upgrade_module.time, "sleep", interrupt)
    assert upgrade("wait", current="1.12.1") == 1
    assert pypi.pip == []


@pytest.mark.skipif(sys.platform == "win32", reason="no clean stop on Windows")
def test_stop_the_processes(pypi):
    pypi.running = [[WATCHER], [WATCHER], []]
    assert upgrade("stop", current="1.12.1") == 0
    assert pypi.killed == [(12345, signal.SIGTERM)] and len(pypi.pip) == 1


@pytest.mark.skipif(sys.platform == "win32", reason="no clean stop on Windows")
def test_a_process_that_cant_be_stopped_cancels_the_upgrade(pypi, monkeypatch):
    pypi.running = [[WATCHER]]

    def denied(pid, sig):
        raise PermissionError("Operation not permitted")
    monkeypatch.setattr(upgrade_module.os, "kill", denied)
    assert upgrade("stop", current="1.12.1") == 1
    assert pypi.pip == []


@pytest.mark.skipif(sys.platform == "win32", reason="no clean stop on Windows")
@pytest.mark.parametrize("answers, action", [(["s"], "stop"), (["x", "Wait"], "wait"), (["f"], "force"),
                                             (["n"], "cancel")])
def test_ask(monkeypatch, answers, action):
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr("builtins.input", lambda question: answers.pop(0))
    assert upgrade_module.ask() == action


def test_ask_ctrl_c_cancels(monkeypatch):
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=lambda: True))

    def interrupt(question):
        raise KeyboardInterrupt
    monkeypatch.setattr("builtins.input", interrupt)
    assert upgrade_module.ask() == "cancel"


@pytest.mark.parametrize("args, action", [([], None), (["--upgrade"], "ask"), (["-upgrade", "check"], "check"),
                                          (["--upgrade", "stop"], "stop")])
def test_upgrade_flag(monkeypatch, args, action):
    from ittup.common.command import CommandLine
    monkeypatch.setattr(sys, "argv", ["ittup", *args])
    assert CommandLine().args.upgrade == action


def test_unknown_upgrade_action(monkeypatch):
    from ittup.common.command import CommandLine
    monkeypatch.setattr(sys, "argv", ["ittup", "--upgrade", "now"])
    with pytest.raises(SystemExit):
        CommandLine()
