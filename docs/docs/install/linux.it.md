# Installazione su Linux

## Requisiti

- **Python 3.10 o superiore** (consigliato: dalla 3.10 alla 3.12 — le versioni più recenti possono dare problemi con alcune librerie)
- **FFmpeg 5.1 o superiore** — usato per estrarre gli screenshot dai video e per controllare i file corrotti
- **Poppler** — solo se vuoi creare torrent di documenti PDF
- **python3-venv** — crea il virtualenv in cui installare ITTup, separato dal Python di sistema

Distribuzioni testate: Ubuntu 24.04, Debian 12.

## 1. Installa le dipendenze

```bash
sudo apt install ffmpeg python3-venv
```

!!! warning "Ubuntu 22.04"
    `apt` installa FFmpeg 4.4, troppo vecchio per il [controllo dei file corrotti](../config/options.md#file-corrotti). Installa una build statica recente in `/usr/local/bin`, che nel `PATH` viene prima di `/usr/bin`:
    ```bash
    wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
    tar xf ffmpeg-release-amd64-static.tar.xz
    sudo cp ffmpeg-*-amd64-static/ffmpeg ffmpeg-*-amd64-static/ffprobe /usr/local/bin/
    ```

    Poi `ffprobe -version` deve mostrare la 5.1 o successiva.

Solo se caricherai documenti PDF:

```bash
sudo apt install poppler-utils
```

## 2. Installa ITTup

ITTup va in un suo **virtualenv**: una cartella con i suoi pacchetti Python, separati da quelli del sistema.

```bash
python3 -m venv ~/.venvs/ittup
~/.venvs/ittup/bin/pip install ittup
```

Per lanciare `ittup` da qualsiasi cartella, collegalo in `~/.local/bin`:

```bash
mkdir -p ~/.local/bin
ln -sf ~/.venvs/ittup/bin/ittup ~/.local/bin/ittup
```

Su Debian e Ubuntu `~/.local/bin` entra nel `PATH` al login, quando la cartella esiste: la prima volta esci e rientra. Lo verifichi con `ittup --help`.

Oppure attiva il virtualenv nel terminale che usi: dopo `source ~/.venvs/ittup/bin/activate` i comandi `ittup` e `pip` sono quelli del virtualenv (`deactivate` per uscire).

!!! warning "Senza virtualenv: solo dove pip lo permette"
    `pip install ittup` senza virtualenv funziona solo con un Python in cui pip può installare pacchetti:
    uno installato da te, o il Python di sistema prima di Debian 12 e Ubuntu 23.04. Su Debian 12+ e
    Ubuntu 23.04+ si ferma con `externally-managed-environment`: non forzarlo con
    `--break-system-packages`, che fa sostituire a pip pacchetti Python del sistema (per esempio
    `typing_extensions`) e fallisce con `uninstall-no-record-file` o rompe strumenti di sistema.

## 3. Primo avvio

```bash
ittup
```

!!! note "Messaggi rossi al primo avvio?"
    È normale: il bot ti sta avvisando che non è ancora configurato. Al primo avvio crea la cartella di configurazione e il file `ittup.json`. Prosegui con la [Configurazione](../config/intro.md).

!!! tip "Sei su una seedbox senza sudo?"
    Vedi la guida dedicata [Seedbox ultra.cc](seedbox.md).
