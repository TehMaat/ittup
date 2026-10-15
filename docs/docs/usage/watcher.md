# Watcher

The watcher is the **automatic** mode: the bot monitors a folder and uploads to the tracker everything that lands in it. Great paired with a client downloading to a fixed folder.

## Start

```bash
ittup -watcher
```

The flag takes no parameters: everything is configured in `ittup.json`.

## Configuration

In `user_preferences` ([Advanced options](../config/options.md#watcher)):

```json
"WATCHER_INTERVAL": 60,
"WATCHER_TIMEOUT": 3600,
"WATCHER_PATH": "/path/source/folder",
"WATCHER_DESTINATION_PATH": "/path/destination/folder",
"WATCHER_QUARANTINE_PATH": "/path/quarantine/folder",
"WATCHER_MAX_RETRIES": 5,
```

- `WATCHER_PATH` → the **watched** folder (e.g. where files get downloaded)
- `WATCHER_DESTINATION_PATH` → the folder where files are **moved** and uploaded from
- `WATCHER_INTERVAL` → how many **seconds** between checks
- `WATCHER_TIMEOUT` → how many **seconds** a single file or folder can take before it's considered stuck (`0` = no limit)
- `WATCHER_QUARANTINE_PATH` → the folder where the **failed** uploads end up (default: `ittup_config/watcher_quarantine_path`)
- `WATCHER_MAX_RETRIES` → how many times an upload stopped by a temporary error is **retried**

## What happens on every cycle

When `WATCHER_INTERVAL` expires:

1. It checks `WATCHER_PATH`; if empty, it waits for the next cycle
2. It **moves** all files to `WATCHER_DESTINATION_PATH`, preserving subfolders (emptied folders are removed), and adds them to the upload **queue**
3. It processes the queue **one at a time**, in alphanumeric order, and **uploads to the tracker** with seeding, like a [`-scan`](upload.md): the files just moved and the retries whose time has come
4. It starts over

The loop is endless: exit with ++ctrl+c++.

!!! note "Countdown and logs"
    In an interactive terminal the countdown is shown on a single line that is cleared when the check starts. When the output goes to a log (file, pipe, `docker logs`, service) there is no countdown: the bot logs `WATCHDOG: checking the Watcher folder every N seconds` once when it goes idle, and then only what actually happens (files moved, uploads).
!!! info "Automatic restart if a file gets stuck"
    Every file or folder is processed separately. If one stops with an error, or is still running after `WATCHER_TIMEOUT` seconds (e.g. ffmpeg stuck on a corrupted file, or a question nobody answers), the bot stops it, logs `... Skipped, restarting the watcher` and goes on with the next one.
    Hashing very large files takes time: if you upload big remuxes from a slow disk, raise `WATCHER_TIMEOUT`.

## Persistent queue and retries

Every moved file goes at once into a **queue saved on disk** (`ittup_config/watcher_queue.json`). If the bot is closed, crashes or the server restarts, the next `ittup -watcher` goes on with the uploads left (`WATCHDOG: N uploads left in the queue by the last run`).

An upload stopped by a **temporary error** — no network, a timeout, a rate limit, the tracker offline or failing (HTTP 5xx), TMDB not answering, a file still running after `WATCHER_TIMEOUT` — is **retried** with a wait that doubles at every attempt: 1, 2, 4, 8, 16 minutes… up to an hour. The log shows `Retry 1/5 in 60 seconds`. While it waits, the watcher keeps uploading the other files.

## Quarantine

An upload that **fails for a reason that doesn't go away by itself** (corrupted file, upload refused by the tracker, unknown resolution or category, a bot error), or that still fails after `WATCHER_MAX_RETRIES` attempts, is **moved to `WATCHER_QUARANTINE_PATH`** instead of staying in the watcher. Next to it there is a `<name>.error.txt` file with the date, the number of attempts and the reason:

```text
Date: 2026-10-15 14:02:11
Path: /watcher/destination/Movie.2020.1080p.mkv
Attempts: 1
Reason:
- 'Movie 2020 1080p WEB-DL H.264': upload refused by the tracker: UploadBot - The name has already been taken. :
```

The `.torrent` that was never uploaded is removed from the archive: once the problem is fixed you can put the file back in `WATCHER_PATH` to try again, or upload it by hand with [`-u`](upload.md).

!!! warning "Files are moved, not copied"
    `WATCHER_PATH` gets **emptied** on every cycle. Don't point it to a folder whose files must stay where they are (e.g. your client's seeding folder).

!!! tip "Folder missing?"
    If `WATCHER_PATH` doesn't exist or isn't configured, the bot stops with `Watcher path does not exist or is not configured`.
