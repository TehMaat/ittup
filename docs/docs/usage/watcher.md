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
```

- `WATCHER_PATH` → the **watched** folder (e.g. where files get downloaded)
- `WATCHER_DESTINATION_PATH` → the folder where files are **moved** and uploaded from
- `WATCHER_INTERVAL` → how many **seconds** between checks
- `WATCHER_TIMEOUT` → how many **seconds** a single file or folder can take before it's considered stuck (`0` = no limit)

## What happens on every cycle

When `WATCHER_INTERVAL` expires:

1. It checks `WATCHER_PATH`; if empty, it waits for the next cycle
2. It **moves** all files to `WATCHER_DESTINATION_PATH`, preserving subfolders (emptied folders are removed)
3. It processes the moved files **one at a time** and **uploads them to the tracker** with seeding, like a [`-scan`](upload.md)
4. It starts over

The loop is endless: exit with ++ctrl+c++.

!!! note "Countdown and logs"
    In an interactive terminal the countdown is shown on a single line that is cleared when the check starts. When the output goes to a log (file, pipe, `docker logs`, service) there is no countdown: the bot logs `WATCHDOG: checking the Watcher folder every N seconds` once when it goes idle, and then only what actually happens (files moved, uploads).
!!! info "Automatic restart if a file gets stuck"
    Every file or folder is processed separately. If one stops with an error, or is still running after `WATCHER_TIMEOUT` seconds (e.g. ffmpeg stuck on a corrupted file, or a question nobody answers), the bot stops it, logs `... Skipped, restarting the watcher` and goes on with the next one.
    The skipped file stays in `WATCHER_DESTINATION_PATH` and is not retried: check it and upload it by hand with [`-u`](upload.md).
    Hashing very large files takes time: if you upload big remuxes from a slow disk, raise `WATCHER_TIMEOUT`.

!!! warning "Files are moved, not copied"
    `WATCHER_PATH` gets **emptied** on every cycle. Don't point it to a folder whose files must stay where they are (e.g. your client's seeding folder).

!!! tip "Folder missing?"
    If `WATCHER_PATH` doesn't exist or isn't configured, the bot stops with `Watcher path does not exist or is not configured`.
