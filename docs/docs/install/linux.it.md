# Installazione su Linux

## Requisiti

- **Python 3.10 o superiore** (consigliato: dalla 3.10 alla 3.12 — le versioni più recenti possono dare problemi con alcune librerie)
- **FFmpeg 5.1 o superiore** — usato per estrarre gli screenshot dai video e per controllare i file corrotti
- **Poppler** — solo se vuoi creare torrent di documenti PDF
- **pipx** — installa ITTup in un ambiente tutto suo, separato dal Python di sistema

Distribuzioni testate: Ubuntu 24.04, Debian 12.

## 1. Installa le dipendenze

```bash
sudo apt install ffmpeg pipx
pipx ensurepath
```

`pipx ensurepath` aggiunge `~/.local/bin` al tuo `PATH`: apri un nuovo terminale dopo averlo eseguito.

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

```bash
pipx install ittup
```

!!! warning "Non usare `pip install` né `--break-system-packages`"
    Su Debian 12+ e Ubuntu 23.04+ un semplice `pip install` si ferma con `externally-managed-environment`.
    Forzarlo con `--break-system-packages` fa sì che pip provi a sostituire pacchetti Python del
    sistema (per esempio `typing_extensions`): fallisce con `uninstall-no-record-file` o può rompere
    strumenti di sistema. Con pipx eviti entrambi i problemi.

## 3. Primo avvio

```bash
ittup
```

!!! note "Messaggi rossi al primo avvio?"
    È normale: il bot ti sta avvisando che non è ancora configurato. Al primo avvio crea la cartella di configurazione e il file `ittup.json`. Prosegui con la [Configurazione](../config/intro.md).

!!! tip "Sei su una seedbox senza sudo?"
    Vedi la guida dedicata [Seedbox ultra.cc](seedbox.md).
