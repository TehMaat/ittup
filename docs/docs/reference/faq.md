# FAQ / Troubleshooting

## First run and configuration

### Red messages on first run

Normal: the bot has just created `ittup.json` and the support files with placeholder values, and it's warning you that the keys are missing. Follow [Getting started](../config/intro.md).

### `-> Please Fix 'FIELD' ['value'] in settings.json`

A value in `ittup.json` is malformed (nonexistent color, non-numeric number, URL without scheme…). Open the file and fix the quoted field. The [Full config reference](config.md) lists the type and allowed values of every key.

### `'-mt' has been removed: ITTup uploads only to ItaTorrents`

`-mt` and `-tracker` came from Unit3Dup and no longer exist: every upload goes to ItaTorrents. Drop the flag from your command or script.

### `-> No PID value for ITT_PID`

`ITT_PID` still holds a placeholder: enter your ITT passkey. See [Tracker](../config/trackers.md).

## Torrent client

### `Unknown Torrent Client name 'xxx'`

`TORRENT_CLIENT` must be exactly `qbittorrent`, `transmission` or `rtorrent`. See [Torrent clients](../config/clients.md).

### The bot can't connect to the client

- Is the WebUI enabled? (qBittorrent: *Tools → Options → WebUI*)
- Host and port correct? (`QBIT_HOST`/`QBIT_PORT` and equivalents)
- Credentials correct?
- Client on another machine/container? Then you also need `SHARED_*_PATH` ([details](../config/clients.md#shared__path-client-on-another-machine))

### Upload without a client?

Yes: `-noseed` uploads without seeding, `-noup` only creates the `.torrent`. The difference: with `-noseed` the torrent **reaches the tracker**, with `-noup` it doesn't — it only stays in the local archive.

## Dependencies

### `ffmpeg` not found

FFmpeg is not in the PATH. [Windows](../install/windows.md#1-install-ffmpeg) · [Linux](../install/linux.md): `sudo apt install ffmpeg`. After adding it to the PATH, close and reopen the terminal.

### `[FFMPEG-ffprobe too old]`

The corrupted files check (`CHECK_CORRUPTED`) needs ffprobe 5.1 or newer. On Ubuntu 22.04 `apt` installs 4.4: [install a static build](../install/linux.md#1-install-the-dependencies), or set `CHECK_CORRUPTED` to `False`.

### `pdftocairo` not recognized

Poppler is missing or not in the PATH — only needed for PDFs. [Windows](../install/windows.md#2-poppler-pdf-only) · Linux: `sudo apt install poppler-utils`.

## Upload

### `There are no Media to process`

Nothing in the path is recognized as media, or the path is wrong or unreadable.

### `Invalid -force category`

Valid categories for `-force` are: `movie`, `tv`, `game`, `edicola`.

### `Skipping game upload, no IGDB credentials provided`

`IGDB_CLIENT_ID` / `IGDB_ID_SECRET` are missing: games are skipped, everything else continues. See [Games](../guides/games.md).

### The title is recognized incorrectly

Use `-notitle "Correct Title"` to force the TMDB search, `-tag` to set the release group, and `TAGS_POSITION_*` to choose the tags. See [Tags and titles](../usage/tags.md).

### `-int` or `-fl100` are not applied

The tracker accepts them only from staff and from the members of an internal group: for the other accounts it uploads the torrent without them, with no error. After the upload the bot reads the torrent back and reports it with a `-int: ...` or `-fl100: ...` warning. See [Basic upload](../usage/upload.md).

### The duplicate check doesn't find a torrent that is already on the tracker

The bot searches by title and, for movies and TV shows, by TMDB ID: check `Duplicate check: N torrents on the tracker for '...'` in the log. A torrent with another resolution or of another category is not a duplicate, nor is one whose size is out of `SIZE_TH`. See [Duplicates](../config/options.md#duplicates).

### Where do the created `.torrent` files go?

Into `TORRENT_ARCHIVE_PATH`, in the `ITT` subfolder: `<archive>/ITT/name.torrent`. Default: `ittup_config/torrent_archive_path/`.

## Watcher

### `Watcher path does not exist or is not configured`

`WATCHER_PATH` doesn't exist or is still `no_path`. Configure both watcher paths ([details](../usage/watcher.md)).

### A file ended up in `watcher_quarantine_path`

The upload failed for a reason that doesn't go away by itself (corrupted file, upload refused by the tracker…) or still failed after `WATCHER_MAX_RETRIES` attempts. The reason is in the `<name>.error.txt` file next to it. Once the problem is fixed, put the file back in `WATCHER_PATH` or upload it with `-u`. See [Quarantine](../usage/watcher.md#quarantine).

### `Retry 1/5 in 60 seconds`

A temporary error (network, tracker offline, rate limit): the watcher retries by itself with a wait that doubles at every attempt, and meanwhile uploads the other files. See [Persistent queue and retries](../usage/watcher.md#persistent-queue-and-retries).

## Other

### Does the bot work on a seedbox without sudo?

Yes, with uv, which also brings a Python that already includes sqlite3: [ultra.cc seedbox](../install/seedbox.md) guide.

### How do I upgrade?

`pip install ittup --upgrade` — [Upgrade](../install/upgrade.md).

### Where do I ask for help?

On [Discord](https://discord.gg/VMYaVzq2AF) or by opening a [GitHub issue](https://github.com/TehMaat/ittup/issues).
