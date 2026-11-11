# Installation on Linux

## Requirements

- **Python 3.10 or newer** (recommended: 3.10 to 3.12 — newer versions may have issues with some libraries)
- **FFmpeg 5.1 or newer** — used to extract screenshots from videos and to check the corrupted files
- **Poppler** — only if you want to create torrents for PDF documents
- **python3-venv** — creates the virtualenv ITTup is installed in, separate from the system Python

Tested distributions: Ubuntu 24.04, Debian 12.

## 1. Install the dependencies

```bash
sudo apt install ffmpeg python3-venv
```

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

ITTup goes in its own **virtualenv**: a folder with its own Python packages, separate from the system ones.

```bash
python3 -m venv ~/.venvs/ittup
~/.venvs/ittup/bin/pip install ittup
```

To run `ittup` from any folder, link it into `~/.local/bin`:

```bash
mkdir -p ~/.local/bin
ln -sf ~/.venvs/ittup/bin/ittup ~/.local/bin/ittup
```

On Debian and Ubuntu `~/.local/bin` is added to the `PATH` at login once it exists: the first time, log out and back in. `ittup --help` checks it.

Or activate the virtualenv in the terminal you use: after `source ~/.venvs/ittup/bin/activate` the `ittup` and `pip` commands are the virtualenv's ones (`deactivate` to leave it).

!!! warning "Without a virtualenv: only where pip allows it"
    `pip install ittup` without a virtualenv works only with a Python that lets pip install packages:
    one you installed yourself, or the system Python before Debian 12 and Ubuntu 23.04. On Debian 12+
    and Ubuntu 23.04+ it stops with `externally-managed-environment`: don't force it with
    `--break-system-packages`, which makes pip replace Python packages owned by the system (for example
    `typing_extensions`) and fails with `uninstall-no-record-file` or breaks system tools.

## 3. First run

```bash
ittup
```

!!! note "Red messages on first run?"
    That's expected: the bot is telling you it's not configured yet. On first run it creates the configuration folder and the `ittup.json` file. Continue with the [Configuration](../config/intro.md).

!!! tip "On a seedbox without sudo?"
    See the dedicated guide: [ultra.cc seedbox](seedbox.md).
