# Advanced options

`user_preferences` section of `ittup.json` (plus `console_options` at the bottom). None of these options is required: the defaults are fine to start with.

## Screenshots

```json
"NUMBER_OF_SCREENSHOTS": 4,
"COMPRESS_SCSHOT": 3,
"RESIZE_SCSHOT": "False",
"WEBP_ENABLED": "False",
```

| Key | Effect |
|---|---|
| `NUMBER_OF_SCREENSHOTS` | How many screenshots to extract from the video |
| `COMPRESS_SCSHOT` | Image compression level |
| `RESIZE_SCSHOT` | Resize screenshots before uploading |
| `WEBP_ENABLED` | Adds an animated webp to the torrent description |

Screenshots are taken evenly between 10% and 90% of the video. A frame that is too dark is replaced with a brighter one close to it. HDR videos (HDR10, HDR10+, HLG, Dolby Vision with an HDR10 base layer) are tone mapped to SDR, so the colors don't look washed out: this needs an ffmpeg build with the `zscale` filter (libzimg), included in the common builds.

## Duplicates

```json
"DUPLICATE_ON": "true",
"SKIP_DUPLICATE": "false",
"SIZE_TH": 10,
```

| Key | Effect |
|---|---|
| `DUPLICATE_ON` | Enables the duplicate check before every upload (same as the `-dup` flag) |
| `SKIP_DUPLICATE` | Skips the content when a duplicate is found, without asking |
| `SIZE_TH` | Percentage threshold: a torrent on the tracker counts as "same content" if its size differs from your file within this percentage |

## Cache

```json
"CACHE_PATH": "no_path",
"CACHE_SCR": "False",
"CACHE_DBONLINE": "False",
"TMDB_DEBUG": "False",
```

| Key | Effect |
|---|---|
| `CACHE_PATH` | Cache folder (default: `ittup_config/cache_path`) |
| `CACHE_SCR` | Reuses screenshots already extracted |
| `CACHE_DBONLINE` | Caches TMDB results and online searches |
| `TMDB_DEBUG` | Logs the TMDB title-matching scores (title, original, alternative titles, translations). Makes extra HTTP requests: keep it off unless you are debugging a wrong match |

## Language, anonymity and signature

```json
"PREFERRED_LANG": "all",
"ANON": "False",
"PERSONAL_RELEASE": "False",
"RELEASER_SIGN": "",
"TORRENT_COMMENT": "no_comment",
```

| Key | Effect |
|---|---|
| `PREFERRED_LANG` | Preferred language code (ISO 3166, e.g. `it`) or `all`: the bot warns when the audio doesn't match |
| `ANON` | **Anonymous** upload: your username doesn't appear on the torrent page |
| `PERSONAL_RELEASE` | Marks every upload as a personal release (same as the `-personal` flag) |
| `RELEASER_SIGN` | Your releaser signature, appended to the title (max 20 characters; see [Tags and titles](../usage/tags.md)) |
| `TORRENT_COMMENT` | Comment embedded in the `.torrent` file |

## Tag order in the title

```json
"TAGS_POSITION_MOVIE": ["title", "year", "part", "version", "resolution", "uhd", "platform", "source", "remux", "multi", "acodec", "channels", "flag", "subtitle", "hdr", "vcodec"],
"TAGS_POSITION_SERIE": ["title", "season", "version", "resolution", "uhd", "platform", "source", "remux", "multi", "acodec", "channels", "flag", "subtitle", "hdr", "vcodec"],
```

The **order** in which tags build the torrent title, for movies and TV shows. You can reorder or remove entries (minimum 5); names must stay within the allowed set. Details: [Tags and titles](../usage/tags.md).

## Rename the files as the title

```json
"RENAME_FILES": "False",
```

With `True` the bot **renames the original files on disk** as the title shown on the tracker, with dots instead of spaces, before creating the torrent: `movie.2021.1080p.web-dl.mkv` becomes `Spider-Man.No.Way.Home.2021.1080p.WEB-DL.DD+.5.1.ITA.ENG.H.264.mkv`. It works with `-u`, `-f`, `-scan` and `-watcher`, for movies and TV shows.

For a folder, the folder takes the title; the video file of a movie folder takes it too, and in a season pack each episode takes the title with its own `SxxExx`. A folder with more movies keeps the file names. Characters that are not valid in a file name (`:` `?` `*`…) are removed.

!!! warning "Files seeded elsewhere"
    A renamed file is no longer found by the clients that were already seeding it with its old name.

## Corrupted files

```json
"CHECK_CORRUPTED": "True",
```

Before the upload, `ffprobe` reads every video file (the file, or each video of a folder) and decodes a few frames at the start, middle and end. A file that can't be read, has damaged data or is truncated (e.g. a download that didn't finish) is not uploaded: the error is shown and the bot moves on to the next one. It takes less than a second per file. Set it to `False` to skip the check.

## Watcher

```json
"WATCHER_INTERVAL": 60,
"WATCHER_TIMEOUT": 3600,
"WATCHER_PATH": "no_path",
"WATCHER_DESTINATION_PATH": "no_path",
```

| Key | Effect |
|---|---|
| `WATCHER_INTERVAL` | How many **seconds** between watcher checks |
| `WATCHER_TIMEOUT` | Maximum **seconds** to process a single file or folder: if it's still running, it's stopped and skipped. `0` = no limit |
| `WATCHER_PATH` | Watched folder (e.g. where your client downloads) |
| `WATCHER_DESTINATION_PATH` | Folder where files are moved and then uploaded |

How it works: [Watcher](../usage/watcher.md).

## Paths

```json
"TORRENT_ARCHIVE_PATH": "no_path",
```

Folder where the bot archives the generated `.torrent` files, inside the `ITT` subfolder (`<archive>/ITT/...`). With `no_path` it uses the default inside `ittup_config`.

## YouTube

```json
"YOUTUBE_PREF_LANG": "IT",
"SKIP_YOUTUBE": "true",
"SKIP_TMDB": "false",
```

| Key | Effect |
|---|---|
| `YOUTUBE_PREF_LANG` | Country/language code (ISO 3166, e.g. `IT`) used to search trailers on YouTube |
| `SKIP_YOUTUBE` | Skips the YouTube trailer search entirely |
| `SKIP_TMDB` | Skips the TMDB lookup (not recommended for videos) |

## FAST_LOAD

```json
"FAST_LOAD": "0",
```

Limits how many items are processed per run (useful values: 1–150; `0` = no limit). Handy to test a `-scan` on a huge folder without processing all of it.

## Console colors (`console_options`)

```json
"console_options": {
    "NORMAL_COLOR": "blue bold",
    "ERROR_COLOR": "red bold",
    "WELCOME_MESSAGE": "https://itatorrents.xyz",
    "WELCOME_MESSAGE_COLOR": "blue",
    "WELCOME_MESSAGE_BORDER_COLOR": "yellow",
    "PANEL_MESSAGE_COLOR": "blue",
    "PANEL_MESSAGE_BORDER_COLOR": "yellow",
    "QUESTION_MESSAGE_COLOR": "yellow"
}
```

Customize the console text and colors. Allowed colors: `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`, plus the `bold` variant (e.g. `"cyan bold"`).
