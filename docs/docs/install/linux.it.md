# Installazione su Linux

## Requisiti

- **Python 3.10 o superiore** (consigliato: dalla 3.10 alla 3.12 — le versioni più recenti possono dare problemi con alcune librerie)
- **FFmpeg** — usato per estrarre gli screenshot dai video
- **Poppler** — solo se vuoi creare torrent di documenti PDF
- **Git** — `pip` lo usa per installare ittup direttamente da GitHub

Distribuzioni testate: Ubuntu 22, Debian 12.

## 1. Installa le dipendenze

```bash
sudo apt install ffmpeg git
```

Solo se caricherai documenti PDF:

```bash
sudo apt install poppler-utils
```

## 2. Installa ittup

```bash
pip install git+https://github.com/TehMaat/ittup
```

## 3. Primo avvio

```bash
ittup
```

!!! note "Messaggi rossi al primo avvio?"
    È normale: il bot ti sta avvisando che non è ancora configurato. Al primo avvio crea la cartella di configurazione e il file `ittup.json`. Prosegui con la [Configurazione](../config/intro.md).

!!! tip "Sei su una seedbox senza sudo?"
    Vedi la guida dedicata [Seedbox ultra.cc](seedbox.md).
