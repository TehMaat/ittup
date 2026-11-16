# Upgrade

When a new version is out:

!!! tip
    At every start the bot asks PyPI for the latest version and, when a newer one is out, shows `ITTup X.Y.Z is available (installed: ...)` after the configuration summary, with the link to its release notes and the other ITTup processes running. It is only a message: the bot goes on with the installed version, and without an answer from PyPI within a second nothing is shown. Only releases are announced, never the [release candidates](rc.md).

## With `ittup --upgrade`

```bash
ittup --upgrade
```

It installs the new version with the `pip` of the Python that runs ITTup (the same virtualenv). If a watcher, a scan, a reseed or an upload is still running, upgrading would stop it halfway or leave it running the old code: they are listed, and the bot asks what to do.

```text
⚠ ITTup processes running: 1
  PID 12345   watcher   started 2026-10-16 10:02   working on: Film.2024.1080p.mkv
Upgrading now can stop an upload halfway.
[W]ait for them to end / [S]top them and upgrade (a watcher ends its upload first) / [F]orce the upgrade / [N]o, cancel:
```

| Answer | Argument | What happens |
|---|---|---|
| Wait | `ittup --upgrade wait` | Waits for them to end, then upgrades |
| Stop | `ittup --upgrade stop` | Sends them a SIGTERM: a watcher ends the upload it is doing and exits, the other commands stop at once. Then upgrades. Not on Windows |
| Force | `ittup --upgrade force` | Upgrades at once: restart them afterwards |
| No | — | Cancels |

The arguments answer the question in a script or a cron job; without a terminal and without an argument the upgrade is cancelled. `ittup --upgrade check` only checks: exit code 0 when ITTup is up to date, 1 when a new version is out, 2 when PyPI doesn't answer.

A watcher that sees a new version installed under it (for example with `pip` by hand) stops before its next upload: restart it.

## With pip

Upgrade with the `pip` of the environment ITTup is installed in. In a virtualenv (as in the [Linux](linux.md) and [ultra.cc seedbox](seedbox.md) guides):

```bash
~/.venvs/ittup/bin/pip install --upgrade ittup
```

Without a virtualenv (as in the [Windows](windows.md) guide), or with the virtualenv activated:

```bash
pip install --upgrade ittup
```

Without `--pre`, pip installs only releases and never goes back to an older version.

!!! note "Installed with pipx or uv tool?"
    Older versions of these guides installed the bot with pipx (Linux) or `uv tool` (seedbox). Switch to a virtualenv once: `pipx uninstall ittup` or `uv tool uninstall ittup`, then install it again following the guide. The configuration in `ittup_config` is kept.

!!! note "Installed from GitHub?"
    Up to 1.5.0 the bot was installed from GitHub (`git+https://github.com/TehMaat/ittup`). It is now on [PyPI](https://pypi.org/project/ittup/): switch to PyPI once with `pip install --upgrade ittup`, then upgrade with the commands above.

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

The old folder is left untouched: from now on edit only the files in `ittup_config`.

Settings of the removed trackers (`SIS_*`, `PTT_*`, `AST_*`) and `MULTI_TRACKER` are simply ignored, and the `-tracker` / `-mt` flags no longer exist: every upload goes to ItaTorrents.

!!! note "Your custom paths are kept"
    `TORRENT_ARCHIVE_PATH`, `CACHE_PATH` and the watcher paths are copied as they are: if they pointed inside `Unit3Dup_config`, they keep doing so. Set them to `no_path` to use the new defaults inside `ittup_config`.

## Keeping Unit3Dup

You don't have to uninstall Unit3Dup: the two can be installed side by side. They have different commands (`unit3dup` and `ittup`), all of ITTup's code lives in the single `ittup` package, and each one has its own configuration folder.

If you use both, keep in mind that:

- The custom paths copied from your Unit3Dup configuration (see the note above) are shared by the two tools. Don't run both watchers on the same folder, or the same files can be uploaded twice: give ITTup its own folders in `ittup.json`, or set them to `no_path`.
- If your Unit3Dup is older than 0.14.x, installing ITTup in the same environment may upgrade libraries Unit3Dup depends on. To keep them isolated, install ITTup in its own virtualenv, as in the [Linux](linux.md) guide.

When you no longer need Unit3Dup, remove it — this also removes the old top-level `common`, `view` and `unit3dup` modules it installed:

```bash
pip uninstall unit3dup
```
