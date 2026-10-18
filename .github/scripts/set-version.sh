#!/usr/bin/env bash
# Writes a PEP 440 version in pyproject.toml, only in the CI workspace: the version committed on main
# stays the one release-please writes.
# usage: set-version.sh <version>
set -euo pipefail
version="$1"
python - "$version" <<'PY'
import re, sys
from packaging.version import Version

version = sys.argv[1]
if str(Version(version)) != version:
    sys.exit(f"'{version}' is not a normalized PEP 440 version (expected e.g. 1.13.0rc1, 1.12.2.dev4)")
with open("pyproject.toml", encoding="utf-8") as file:
    text = file.read()
text, count = re.subn(r'(?m)^version = "[^"]*"$', f'version = "{version}"', text, count=1)
if count != 1:
    sys.exit("no version line in pyproject.toml")
with open("pyproject.toml", "w", encoding="utf-8") as file:
    file.write(text)
print(f"pyproject.toml version: {version}")
PY
