# Release candidate

Before every release, a **release candidate** (rc), for example `1.13.0rc3`, is published on [PyPI](https://pypi.org/project/ittup/#history) for testing: it is the version that will become the release, to try for a few days on real uploads. pip installs a pre-release only when asked with `--pre`, so whoever doesn't ask never gets one.

!!! warning
    An rc can still have bugs: install it if you want to help test it, and [report](#report-a-problem) what doesn't work.

The commands are for Linux, with ITTup in a virtualenv as in the [Linux](linux.md) guide. On Windows use the `pip` of your installation: `pip install --upgrade --pre ittup`.

## Install an rc

In a new virtualenv, so your normal installation stays as it is:

```bash
python3 -m venv ~/.venvs/ittup-rc
~/.venvs/ittup-rc/bin/pip install --pre ittup
~/.venvs/ittup-rc/bin/ittup
```

Or upgrade your normal installation:

```bash
~/.venvs/ittup/bin/pip install --upgrade --pre ittup
```

`--pre` takes the most recent version, rc or release. For a specific rc: `pip install ittup==1.13.0rc3`.

The bot shows the version when it starts (`ITTup 1.13.0rc3 ...`); `pip show ittup` shows it too.

!!! note "The configuration is the same"
    Every installation uses the same `ittup_config` folder. The rc upgrades `ittup.json` like any new version: the new options get their default value and the previous file is kept as `ittup.json.bak-<date>`.

## The next rc

When a new rc comes out (for example `1.13.0rc4`, after a fix):

```bash
~/.venvs/ittup-rc/bin/pip install --upgrade --pre ittup
```

## Back to the release

| Command | What it does |
|---|---|
| `pip install --upgrade ittup` | Without `--pre`, pip takes only releases and never goes back: it stays on the rc until the release after it comes out (`1.13.0rc3` → `1.13.0`), then upgrades. From then on, only releases. |
| `pip install ittup==1.12.1` | Goes back at once to the release you name, for example the previous one. |

With a separate virtualenv, go back to using your normal installation and delete the rc's one: `rm -rf ~/.venvs/ittup-rc`.

Going back to the previous release works with the configuration the rc used: the options it doesn't know are removed from `ittup.json` and stay in the backup.

## Update notice

With an rc installed, the bot announces the release after it (`ITTup 1.13.0 is available (installed: 1.13.0rc3)`), never another rc: to get the next rc, run the command above. Up to `1.13.0rc3` the notice didn't appear with an rc installed: upgrade by hand when the release is out.

## Report a problem

Open a [Bug](https://github.com/TehMaat/ittup/issues/new?template=bug.yml) with channel `rc` and the exact version (`1.13.0rc3`), or write on [Discord](https://discord.gg/VMYaVzq2AF).
