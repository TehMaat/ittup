# Configuration — getting started

## Where the configuration lives

On **first run** the bot creates the `ittup_config` folder containing the main configuration file and the support files:

| System | Path |
|---|---|
| Windows | `%LOCALAPPDATA%\ittup_config\` |
| Linux / macOS | `~/ittup_config/` |

Folder contents:

| File | Purpose |
|---|---|
| `ittup.json` | **Main configuration**: tracker, API keys, torrent client, preferences |
| `tags_list.json` | Custom tags for title building ([details](../usage/tags.md)) |
| `sign_list.json` | Releaser signatures ([details](../usage/tags.md)) |
| `ban_list.json` | Tags to exclude from the title autobuild ([details](../usage/tags.md)) |

!!! note "Coming from Unit3Dup?"
    On the first run ittup copies `Unit3Dup_config/Unit3Dbot.json` and the three lists into `ittup_config` (the old folder is left untouched). Details: [Upgrade](../install/upgrade.md#coming-from-unit3dup).

In the same folder the bot also creates the default subfolders `torrent_archive_path` (where generated `.torrent` files are stored), `cache_path`, `watcher_path` and `watcher_destination_path` — all customizable (see [Advanced options](options.md)).

## File structure

`ittup.json` is split into **five sections**:

```json
{
    "tracker_config": { },
    "torrent_client_config": { },
    "user_preferences": { },
    "options": { },
    "console_options": { }
}
```

| Section | Contents | Page |
|---|---|---|
| `tracker_config` | ITT URL, API key and passkey, TMDB/TVDB/IGDB/YouTube keys, image host keys | [Tracker](trackers.md), [Metadata](metadata.md), [Image hosts](imagehosts.md) |
| `torrent_client_config` | qBittorrent, Transmission, rTorrent | [Torrent clients](clients.md) |
| `user_preferences` | Screenshots, cache, watcher, duplicates, tags, language… | [Advanced options](options.md) |
| `options` | FTP connection | [FTP](../usage/ftp.md) |
| `console_options` | Console colors and messages | [Advanced options](options.md) |

## Minimal configuration

You don't need to fill in every line. To get started you only need:

1. **`ITT_APIKEY` + `ITT_PID`** — [Tracker](trackers.md)
2. **`TMDB_APIKEY`** — [Metadata](metadata.md)
3. **At least two image host keys** — [Image hosts](imagehosts.md)
4. **`TORRENT_CLIENT` + client credentials** — [Torrent clients](clients.md)

Unconfigured values stay `no_key` / `no_pass` / `no_path`.

## Check your configuration

```bash
ittup -check
```

It validates the configuration files and the environment. On startup the bot always prints the active paths:

```text
[Configuration] '~/ittup_config/ittup.json'
[*.torrent Archive] '~/ittup_config/torrent_archive_path'
[Images,Tmdb cache] '~/ittup_config/cache_path'
[Watcher] '~/ittup_config/watcher_path'
[Watcher] '~/ittup_config/watcher_destination_path'
[Preferred Language] 'all'
[Youtube Preferred Language] 'IT'
```

!!! danger "Blocking errors"
    If a value is malformed the bot exits immediately with a message like `-> Please Fix 'FIELD' ['value'] in settings.json`: open `ittup.json` and fix the reported field.
