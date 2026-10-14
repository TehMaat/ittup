# Installation on Linux

## Requirements

- **Python 3.10 or newer** (recommended: 3.10 to 3.12 — newer versions may have issues with some libraries)
- **FFmpeg** — used to extract screenshots from videos
- **Poppler** — only if you want to create torrents for PDF documents
- **Git** — used to install ITTup straight from GitHub
- **pipx** — installs ITTup in its own environment, separate from the system Python

Tested distributions: Ubuntu 22, Debian 12.

## 1. Install the dependencies

```bash
sudo apt install ffmpeg git pipx
pipx ensurepath
```

`pipx ensurepath` adds `~/.local/bin` to your `PATH`: open a new terminal afterwards.

Only if you upload PDF documents:

```bash
sudo apt install poppler-utils
```

## 2. Install ITTup

```bash
pipx install git+https://github.com/TehMaat/ittup
```

!!! warning "Don't use `pip install` or `--break-system-packages`"
    On Debian 12+ and Ubuntu 23.04+ a plain `pip install` stops with `externally-managed-environment`.
    Forcing it with `--break-system-packages` makes pip try to replace Python packages owned by the
    system (for example `typing_extensions`), which fails with `uninstall-no-record-file` or can break
    system tools. pipx avoids both.

## 3. First run

```bash
ittup
```

!!! note "Red messages on first run?"
    That's expected: the bot is telling you it's not configured yet. On first run it creates the configuration folder and the `ittup.json` file. Continue with the [Configuration](../config/intro.md).

!!! tip "On a seedbox without sudo?"
    See the dedicated guide: [ultra.cc seedbox](seedbox.md).
