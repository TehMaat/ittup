# Installazione su Linux

## Requisiti

- **Python 3.10 o superiore** (consigliato: dalla 3.10 alla 3.12 — le versioni più recenti possono dare problemi con alcune librerie)
- **FFmpeg** — usato per estrarre gli screenshot dai video
- **Poppler** — solo se vuoi creare torrent di documenti PDF
- **Git** — serve per installare ITTup direttamente da GitHub
- **pipx** — installa ITTup in un ambiente tutto suo, separato dal Python di sistema

Distribuzioni testate: Ubuntu 22, Debian 12.

## 1. Installa le dipendenze

```bash
sudo apt install ffmpeg git pipx
pipx ensurepath
```

`pipx ensurepath` aggiunge `~/.local/bin` al tuo `PATH`: apri un nuovo terminale dopo averlo eseguito.

Solo se caricherai documenti PDF:

```bash
sudo apt install poppler-utils
```

## 2. Installa ITTup

```bash
pipx install git+https://github.com/TehMaat/ittup
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
