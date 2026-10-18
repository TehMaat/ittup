# -*- coding: utf-8 -*-
"""
The installed ittup starts: CI runs it on the built wheel, in a clean virtualenv
ITTUP_EXPECTED_VERSION, when set, is the version the package must report
"""
import os
import shutil
import subprocess
from importlib.metadata import version

import pytest

pytestmark = pytest.mark.smoke


def test_command_starts(tmp_path):
    command = shutil.which("ittup")
    assert command, "the ittup command is not installed"
    env = {**os.environ, "HOME": str(tmp_path), "LOCALAPPDATA": str(tmp_path)}
    result = subprocess.run([command, "--help"], cwd=tmp_path, env=env, stdin=subprocess.DEVNULL,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr
    assert "usage: ittup" in result.stdout


def test_package_version():
    expected = os.environ.get("ITTUP_EXPECTED_VERSION")
    if not expected:
        pytest.skip("ITTUP_EXPECTED_VERSION not set")
    assert version("ittup") == expected
