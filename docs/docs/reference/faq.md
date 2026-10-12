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

### `pdftocairo` not recognized

Poppler is missing or not in the PATH — only needed for PDFs. [Windows](../install/windows.md#2-poppler-pdf-only) · Linux: `sudo apt install poppler-utils`.

## Upload

### `There are no Media to process`

Nothing in the path is recognized as media, or the path is wrong or unreadable.

### `Invalid -force category`

Valid categories for `-force` are: `movie`, `tv`, `game`, `edicola`.

### `Skipping game upload, no IGDB credentials provided`

`IGDB_CLIENT_ID` / `IGDB_ID_SECRET` are missing: games are skipped, everything else continues. See [Games](../guides/games.md).

### `User tags file ... not found`

`tags_list.json` is missing from the configuration folder. It's created on first run: if you deleted it, launch the bot once with no arguments. See [Tags and titles](../usage/tags.md).

### The title is recognized incorrectly

Use `-notitle "Correct Title"` to force the TMDB search; tweak `tags_list.json` and `ban_list.json` to fix the tags. See [Tags and titles](../usage/tags.md).

### Where do the created `.torrent` files go?

Into `TORRENT_ARCHIVE_PATH`, in the `ITT` subfolder: `<archive>/ITT/name.torrent`. Default: `ittup_config/torrent_archive_path/`.

## Watcher

### `Watcher path does not exist or is not configured`

`WATCHER_PATH` doesn't exist or is still `no_path`. Configure both watcher paths ([details](../usage/watcher.md)).

## Other

### Does the bot work on a seedbox without sudo?

Yes, with uv, which also brings a Python that already includes sqlite3: [ultra.cc seedbox](../install/seedbox.md) guide.

### How do I upgrade?

`pip install --upgrade git+https://github.com/TehMaat/ittup` — [Upgrade](../install/upgrade.md).

### Where do I ask for help?

On [Discord](https://discord.gg/VMYaVzq2AF) or by opening a [GitHub issue](https://github.com/TehMaat/ittup/issues).
