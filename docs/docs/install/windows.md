# Installation on Windows

## Requirements

- **Python 3.10 or newer** (recommended: 3.10 to 3.12 — newer versions may have issues with some libraries)
- **FFmpeg 5.1 or newer** — used to extract screenshots from videos and to check the corrupted files
- **Poppler** — only if you want to create torrents for PDF documents

## 1. Install FFmpeg

1. Download FFmpeg from [ffmpeg.org/download.html](https://www.ffmpeg.org/download.html)
2. Unzip the archive to a folder of your choice (e.g. `C:\ffmpeg`)
3. Add the FFmpeg `bin` folder to your **PATH** environment variable (user)
4. Close and reopen the terminal, then verify:

```bash
ffmpeg -version
```

## 2. Poppler (PDF only)

Needed only if you upload PDF documents — the bot uses it to extract the cover from the first page.

1. Download Poppler for Windows from [github.com/oschwartz10612/poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases)
2. Unzip it and add the `bin` folder to the system PATH (example: `C:\poppler-24.08.0\Library\bin`)
3. **Close and reopen the terminal**
4. Verify the installation:

```bash
pdftocairo -v
```

## 3. Install ITTup

```bash
pip install ittup
```

!!! tip "In a virtualenv"
    To keep ITTup and its packages separate from the other Python programs, install it in a virtualenv (Command Prompt):

    ```bat
    py -m venv %USERPROFILE%\ittup-venv
    %USERPROFILE%\ittup-venv\Scripts\pip install ittup
    ```

    Then start it with `%USERPROFILE%\ittup-venv\Scripts\ittup`, or activate the virtualenv first with `%USERPROFILE%\ittup-venv\Scripts\activate`: the `ittup` and `pip` commands are then the virtualenv's ones.

## 4. First run

```bash
ittup
```

!!! note "Red messages on first run?"
    That's expected: the bot is telling you it's not configured yet. On first run it creates the configuration folder and the `ittup.json` file. Continue with the [Configuration](../config/intro.md).
