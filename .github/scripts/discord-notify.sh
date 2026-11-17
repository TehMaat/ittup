#!/usr/bin/env bash
# Announces a release on the project's Discord channel through a webhook (RELEASING.md, "Discord").
#   discord-notify.sh [--dry-run] rc <X.Y.ZrcN>        notes: the feat:/fix: commits since the last stable tag
#   discord-notify.sh [--dry-run] stable <X.Y.Z> <url>  notes: the release-please notes in $NOTES, url: the release
# The webhook is the secret DISCORD_WEBHOOK_URL: without it the message is skipped. --dry-run prints the JSON.
# A failed post is only a warning: the release is already out, the announcement must not mark it as failed.
set -euo pipefail

dry_run=false
if [ "${1:-}" = --dry-run ]; then dry_run=true; shift; fi
kind="${1:?usage: discord-notify.sh [--dry-run] rc|stable <version> [release url]}"
version="${2:?missing version}"
server="${GITHUB_SERVER_URL:-https://github.com}"
repo="$server/${GITHUB_REPOSITORY:-TehMaat/ittup}"
pypi="https://pypi.org/project/ittup/$version/"

if ! $dry_run && [ -z "${DISCORD_WEBHOOK_URL:-}" ]; then
  echo "::notice::DISCORD_WEBHOOK_URL is not set: no Discord announcement"
  exit 0
fi

# rc: the commits since the last stable tag ($1, empty for none), as release-please will write them in the changelog
rc_notes() {
  local range=HEAD subject type breaking scope text features="" fixes="" breaks=""
  if [ -n "$1" ]; then range="$1..HEAD"; fi
  while IFS= read -r subject; do
    [[ "$subject" =~ ^(feat|fix)(\(([^\)]+)\))?(!)?:\ +(.+)$ ]] || continue
    type="${BASH_REMATCH[1]}" scope="${BASH_REMATCH[3]}" breaking="${BASH_REMATCH[4]}" text="${BASH_REMATCH[5]}"
    [ -n "$scope" ] && text="**$scope:** $text"
    if [ -n "$breaking" ]; then breaks+="- $text"$'\n'
    elif [ "$type" = feat ]; then features+="- $text"$'\n'
    else fixes+="- $text"$'\n'
    fi
  done < <(git log --no-merges --format=%s "$range")
  [ -n "$breaks" ] && printf '**⚠ Modifiche incompatibili**\n%s\n' "$breaks"
  [ -n "$features" ] && printf '**Novità**\n%s\n' "$features"
  [ -n "$fixes" ] && printf '**Correzioni**\n%s\n' "$fixes"
  [ -n "$breaks$features$fixes" ] || printf 'Nessuna novità o correzione.\n'
}

# stable: release-please's notes without its first line (version and date, already in the title), with the
# sections in Italian and bold (Discord embeds don't render ### headings)
stable_notes() {
  sed -E \
    -e '1{/^##? \[?[0-9]/d}' \
    -e 's/^### ⚠ BREAKING CHANGES$/**⚠ Modifiche incompatibili**/' \
    -e 's/^### Features$/**Novità**/' \
    -e 's/^### Bug Fixes$/**Correzioni**/' \
    -e 's/^### (.+)$/**\1**/' \
    -e 's/^\* /- /' <<<"${NOTES:-}" | sed -E '/./,$!d; /^\*\*.+\*\*$/{n;/^$/d}' | cat -s
}

case "$kind" in
  rc)
    last=$(git tag --merged HEAD --list '[0-9]*.[0-9]*.[0-9]*' | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1 || true)
    url="$repo/commits/$version"
    if [ -n "$last" ]; then url="$repo/compare/$last...$version"; fi
    notes=$(rc_notes "$last")
    title="🧪 ITTup $version — versione di prova"
    color=15105570
    install=$'**Installazione**\n```\npip install --upgrade --pre "ittup=='"$version"$'"\n```'
    links="🔗 [Modifiche su GitHub]($url) · [PyPI]($pypi)"
    footer="Provatela per 3-5 giorni e segnalate i problemi con una issue."
    ;;
  stable)
    url="${3:?missing release url}"
    notes=$(stable_notes)
    title="🚀 ITTup $version è uscita"
    color=3066993
    install="**Installa o aggiorna**"$'\n```\npip install --upgrade ittup\n```'
    links="🔗 [Release su GitHub]($url) · [PyPI]($pypi)"
    footer=""
    ;;
  *)
    echo "::error::unknown kind '$kind': rc or stable" >&2
    exit 2
    ;;
esac

# Discord allows 4096 characters in an embed description: long notes are cut at a line and point to GitHub.
# allowed_mentions empty: an @everyone or a mention in a commit subject pings nobody
payload=$(jq -n --arg title "$title" --arg url "$url" --argjson color "$color" --arg notes "$notes" \
  --arg install "$install" --arg links "$links" --arg footer "$footer" '
  ($install + "\n" + $links) as $tail
  | (4000 - ($tail | length)) as $room
  | (if ($notes | length) <= $room then $notes
     else ($notes[:$room - 60] | sub("\n[^\n]*$"; "")) + "\n… [note complete su GitHub](" + $url + ")"
     end) as $body
  | {allowed_mentions: {parse: []},
     embeds: [{title: $title, url: $url, color: $color, description: ($body + "\n\n" + $tail)}
              + (if $footer == "" then {} else {footer: {text: $footer}} end)]}')

if $dry_run; then
  echo "$payload"
  exit 0
fi
if ! curl -fsS --max-time 20 --retry 2 -o /dev/null -H 'Content-Type: application/json' -d "$payload" \
    "$DISCORD_WEBHOOK_URL"; then
  echo "::warning::The Discord announcement of $version failed: post it by hand (RELEASING.md, \"Discord\")"
  exit 0
fi
echo "Announced $version on Discord"
