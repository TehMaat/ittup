# Upgrade

When a new version is out:

!!! tip
    At every start the bot asks PyPI for the latest version and, when a newer one is out, shows `ITTup X.Y.Z is available (installed: ...)` after the configuration summary. It is only a message: the bot goes on with the installed version, and without an answer from PyPI within a second nothing is shown.

```bash
pip install ittup --upgrade
```

If you installed it with pipx (as in the [Linux](linux.md) guide):

```bash
pipx upgrade ittup
```

If you installed it with uv (as in the [ultra.cc seedbox](seedbox.md) guide):

```bash
uv tool upgrade ittup
```

!!! note "Installed from GitHub?"
    Up to 1.5.0 the bot was installed from GitHub (`git+https://github.com/TehMaat/ittup`). It is now on [PyPI](https://pypi.org/project/ittup/): switch to PyPI once with `pip install ittup --upgrade`, `pipx install --force ittup` or `uv tool install --force --python 3.12 ittup`, then upgrade with the commands above.

The installed version is shown when the bot starts:

```text
ITTup 1.1.0 Checking your configuration file..
```

!!! tip "After every upgrade"
    Run a configuration check: new versions may introduce new config keys.

    ```bash
    ittup -check
    ```

Release notes are on the [project Releases page](https://github.com/TehMaat/ittup/releases).

## Coming from Unit3Dup

ITTup is a fork of [Unit3Dup](https://github.com/31December99/Unit3Dup) reduced to ItaTorrents only. To switch:

1. Install ITTup:

    ```bash
    pip install ittup
    ```

2. Launch it once:

    ```bash
    ittup
    ```

On the first run, if `Unit3Dup_config` exists and `ittup_config` does not, ITTup **copies** your configuration into the new folder:

| Unit3Dup | ITTup |
|---|---|
| `Unit3Dup_config/Unit3Dbot.json` | `ittup_config/ittup.json` |
| `Unit3Dup_config/tags_list.json` | `ittup_config/tags_list.json` |
| `Unit3Dup_config/sign_list.json` | `ittup_config/sign_list.json` |
| `Unit3Dup_config/ban_list.json` | `ittup_config/ban_list.json` |

The old folder is left untouched: from now on edit only the files in `ittup_config`.

Settings of the removed trackers (`SIS_*`, `PTT_*`, `AST_*`) and `MULTI_TRACKER` are simply ignored, and the `-tracker` / `-mt` flags no longer exist: every upload goes to ItaTorrents.

!!! note "Your custom paths are kept"
    `TORRENT_ARCHIVE_PATH`, `CACHE_PATH` and the watcher paths are copied as they are: if they pointed inside `Unit3Dup_config`, they keep doing so. Set them to `no_path` to use the new defaults inside `ittup_config`.

## Keeping Unit3Dup

You don't have to uninstall Unit3Dup: the two can be installed side by side. They have different commands (`unit3dup` and `ittup`), all of ITTup's code lives in the single `ittup` package, and each one has its own configuration folder.

If you use both, keep in mind that:

- The custom paths copied from your Unit3Dup configuration (see the note above) are shared by the two tools. Don't run both watchers on the same folder, or the same files can be uploaded twice: give ITTup its own folders in `ittup.json`, or set them to `no_path`.
- If your Unit3Dup is older than 0.14.x, installing ITTup in the same environment may upgrade libraries Unit3Dup depends on. To keep them isolated, install ITTup with pipx or in a virtualenv:

    ```bash
    pipx install ittup
    ```

When you no longer need Unit3Dup, remove it — this also removes the old top-level `common`, `view` and `unit3dup` modules it installed:

```bash
pip uninstall unit3dup
```
