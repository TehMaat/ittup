# Basic upload

The three core flags: `-u`, `-f`, `-scan`. All of them run the full pipeline — analysis, screenshots, metadata lookup, `.torrent` creation, tracker upload, client seeding.

## `-u` — a single file

```bash
ittup -u "/home/ITT/upload/movie.mkv"
```

Uploads **one file**. The bot analyzes it, derives title and tags from the name, creates the torrent.

## `-f` — a folder

```bash
ittup -f "/home/ITT/upload/foldername"
```

Creates **a single torrent with the folder contents**, named after the folder. It can hold a movie or a TV show: the bot doesn't care.

Use it for: full seasons, multi-part movies, content with companion files.

## `-scan` — everything inside a path

```bash
ittup -scan "/home/ITT/upload"
```

It's `-u` and `-f` combined: it analyzes **every file and every folder** inside the path (recursively) and processes everything, one torrent per item found. Items are uploaded in alphanumeric order (`E2` before `E10`).

!!! tip "Too much content?"
    On very large folders you can cap the number of processed items with `FAST_LOAD` in the [Advanced options](../config/options.md).

## Modifiers

They combine with `-u`, `-f` and `-scan`:

| Flag | Effect |
|---|---|
| `-noup` | Creates the `.torrent` only (in the [archive](../config/options.md#paths)), **no upload** and no seeding |
| `-noseed` | Upload to the tracker **without seeding**: the torrent is not handed to the client |
| `-dup` | Checks the tracker for [duplicates](../config/options.md#duplicates) before uploading |
| `-personal` | Marks the upload as a **personal release** |
| `-force <category>` | Forces the category: `movie`, `tv`, `game`, `edicola` (without argument: `movie`) |
| `-notitle "<title>"` | Uses this title for the TMDB search instead of the one derived from the file name |
| `-reseed` | Reseed mode ([Reseed](reseed.md)) |

## IDs in the name

If the file or folder name carries an ID, the bot uses it instead of searching TMDB by title:

```text
The Matrix (1999) {imdb-tt0133093}.mkv
The Matrix (1999) {tmdb-603}.mkv
The Matrix (1999) [tmdbid-603].mkv
The Matrix (1999) (tmdb-603).mkv
The.Matrix.1999.tt0133093.1080p.mkv
```

The `{imdb-tt…}` format is the one used by Radarr, Sonarr and Plex, `[tmdbid-…]` the Jellyfin one; round brackets, `=` instead of the dash (Emby) and the IMDB ID alone (`tt0133093`) work too. With the IMDB ID only, the bot asks TMDB for the matching TMDB ID; with the TMDB ID only, it takes the IMDB ID from TMDB. Both are sent to the tracker. The tag is removed from the title shown on the tracker.

Without an ID, the bot searches TMDB for the title taken from the name. When it isn't found it retries with the whole name before the year (`(500) Days of Summer`) and with the titles in brackets (`Lo Chiamavano Jeeg Robot (They Call Me Jeeg)`), and finally with a year tolerance: one year for movies (end-of-year releases), the year of a later season for TV shows.

## Full example

```bash
ittup -dup -u "/home/parzival/TEST/scan/007 - Live and Let Die (1973).mkv"
```

Analyzes the file, builds title and tags, checks ItaTorrents for duplicates, uploads it and starts seeding.

!!! note "What you see on screen"
    The bot prints a table of the files being processed, then for each item: TMDB lookup, screenshot extraction, image upload, torrent creation, tracker response, hand-off to the client. The [First upload step by step](../guides/first-upload.md) guide describes every stage.
