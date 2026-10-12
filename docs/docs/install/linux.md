# Installation on Linux

## Requirements

- **Python 3.10 or newer** (recommended: 3.10 to 3.12 — newer versions may have issues with some libraries)
- **FFmpeg** — used to extract screenshots from videos
- **Poppler** — only if you want to create torrents for PDF documents
- **Git** — `pip` uses it to install ittup straight from GitHub

Tested distributions: Ubuntu 22, Debian 12.

## 1. Install the dependencies

```bash
sudo apt install ffmpeg git
```

Only if you upload PDF documents:

```bash
sudo apt install poppler-utils
```

## 2. Install ittup

```bash
pip install git+https://github.com/TehMaat/ittup
```

## 3. First run

```bash
ittup
```

!!! note "Red messages on first run?"
    That's expected: the bot is telling you it's not configured yet. On first run it creates the configuration folder and the `ittup.json` file. Continue with the [Configuration](../config/intro.md).

!!! tip "On a seedbox without sudo?"
    See the dedicated guide: [ultra.cc seedbox](seedbox.md).
