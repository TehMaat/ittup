#!/usr/bin/env bash
# Fails when a check reports more errors than its baseline in .github/quality-baseline.conf
# usage: ratchet.sh <name> <count> <max>
set -euo pipefail
name="$1" count="$2" max="$3"
echo "$name: $count errors (baseline $max)"
if [ "$count" -gt "$max" ]; then
  echo "::error::$name reports $count errors, more than the $max of the baseline: fix the new ones"
  exit 1
fi
if [ "$count" -lt "$max" ]; then
  echo "::notice::$name is down to $count errors: lower its baseline in .github/quality-baseline.conf to $count"
fi
