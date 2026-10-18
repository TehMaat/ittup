#!/usr/bin/env bash
# The dev version of HEAD: the patch after the latest release plus the number of commits of HEAD,
# e.g. 1.12.2.dev812. It sorts after the latest release and before any next one, so pip never prefers it
# without --pre, and it grows with every commit on dev. The latest release is the highest release tag,
# also when it is a hotfix on main that dev doesn't contain yet.
set -euo pipefail
last=$(git tag --list '[0-9]*.[0-9]*.[0-9]*' | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1)
if [ -z "$last" ]; then
  echo "::error::No release tag: fetch with fetch-depth: 0" >&2
  exit 1
fi
IFS=. read -r major minor patch <<<"$last"
echo "${major}.${minor}.$((patch + 1)).dev$(git rev-list --count HEAD)"
