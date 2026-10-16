# Installation on Linux

## Requirements

- **Python 3.10 or newer** (recommended: 3.10 to 3.12 — newer versions may have issues with some libraries)
- **FFmpeg 5.1 or newer** — used to extract screenshots from videos and to check the corrupted files
- **Poppler** — only if you want to create torrents for PDF documents
- **pipx** — installs ITTup in its own environment, separate from the system Python

Tested distributions: Ubuntu 24.04, Debian 12.

## 1. Install the dependencies

```bash
sudo apt install ffmpeg pipx
pipx ensurepath
```

`pipx ensurepath` adds `~/.local/bin` to your `PATH`: open a new terminal afterwards.

!!! warning "Ubuntu 22.04"
    `apt` installs FFmpeg 4.4, too old for the [corrupted files check](../config/options.md#corrupted-files). Install a recent static build in `/usr/local/bin`, which comes before `/usr/bin` in the `PATH`:
    ```bash
    wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
    tar xf ffmpeg-release-amd64-static.tar.xz
    sudo cp ffmpeg-*-amd64-static/ffmpeg ffmpeg-*-amd64-static/ffprobe /usr/local/bin/
    ```

    `ffprobe -version` must then show 5.1 or newer.

Only if you upload PDF documents:

```bash
sudo apt install poppler-utils
```

## 2. Install ITTup

```bash
pipx install ittup
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
