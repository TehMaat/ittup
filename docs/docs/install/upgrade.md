# Upgrade

When a new version is out:

```bash
pip install --upgrade git+https://github.com/TehMaat/ittup
```

The installed version is shown when the bot starts:

```text
ittup 1.1.0 Checking your configuration file..
```

!!! tip "After every upgrade"
    Run a configuration check: new versions may introduce new config keys.

    ```bash
    ittup -check
    ```

Release notes are on the [project Releases page](https://github.com/TehMaat/ittup/releases).

## Coming from Unit3Dup

ittup is a fork of [Unit3Dup](https://github.com/31December99/Unit3Dup) reduced to ItaTorrents only. To switch:

1. Uninstall Unit3Dup — this also removes the old top-level `common`, `view` and `unit3dup` modules it left behind:

    ```bash
    pip uninstall unit3dup
    ```

2. Install ittup:

    ```bash
    pip install git+https://github.com/TehMaat/ittup
    ```

3. Launch it once:

    ```bash
    ittup
    ```

On the first run, if `Unit3Dup_config` exists and `ittup_config` does not, ittup **copies** your configuration into the new folder:

| Unit3Dup | ittup |
|---|---|
| `Unit3Dup_config/Unit3Dbot.json` | `ittup_config/ittup.json` |
| `Unit3Dup_config/tags_list.json` | `ittup_config/tags_list.json` |
| `Unit3Dup_config/sign_list.json` | `ittup_config/sign_list.json` |
| `Unit3Dup_config/ban_list.json` | `ittup_config/ban_list.json` |

The old folder is left untouched: from now on edit only the files in `ittup_config`.

Settings of the removed trackers (`SIS_*`, `PTT_*`, `AST_*`) and `MULTI_TRACKER` are simply ignored, and the `-tracker` / `-mt` flags no longer exist: every upload goes to ItaTorrents.

!!! note "Your custom paths are kept"
    `TORRENT_ARCHIVE_PATH`, `CACHE_PATH` and the watcher paths are copied as they are: if they pointed inside `Unit3Dup_config`, they keep doing so. Set them to `no_path` to use the new defaults inside `ittup_config`.
