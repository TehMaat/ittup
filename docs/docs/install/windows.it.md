# Installazione su Windows

## Requisiti

- **Python 3.10 o superiore** (consigliato: dalla 3.10 alla 3.12 — le versioni più recenti possono dare problemi con alcune librerie)
- **FFmpeg 5.1 o superiore** — usato per estrarre gli screenshot dai video e per controllare i file corrotti
- **Poppler** — solo se vuoi creare torrent di documenti PDF

## 1. Installa FFmpeg

1. Scarica FFmpeg da [ffmpeg.org/download.html](https://www.ffmpeg.org/download.html)
2. Decomprimi l'archivio in una cartella a piacere (es. `C:\ffmpeg`)
3. Aggiungi la cartella `bin` di FFmpeg alla variabile d'ambiente **PATH** (utente)
4. Chiudi e riapri il terminale, poi verifica:

```bash
ffmpeg -version
```

## 2. Poppler (solo per i PDF)

Serve soltanto se caricherai documenti PDF — il bot lo usa per estrarre la cover dalla prima pagina.

1. Scarica Poppler per Windows da [github.com/oschwartz10612/poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases)
2. Decomprimi e aggiungi la cartella `bin` al PATH di sistema (esempio: `C:\poppler-24.08.0\Library\bin`)
3. **Chiudi e riapri il terminale**
4. Verifica l'installazione:

```bash
pdftocairo -v
```

## 3. Installa ITTup

```bash
pip install ittup
```

!!! tip "In un virtualenv"
    Per tenere ITTup e i suoi pacchetti separati dagli altri programmi Python, installalo in un virtualenv (Prompt dei comandi):

    ```bat
    py -m venv %USERPROFILE%\ittup-venv
    %USERPROFILE%\ittup-venv\Scripts\pip install ittup
    ```

    Poi avvialo con `%USERPROFILE%\ittup-venv\Scripts\ittup`, oppure attiva prima il virtualenv con `%USERPROFILE%\ittup-venv\Scripts\activate`: i comandi `ittup` e `pip` sono allora quelli del virtualenv.

## 4. Primo avvio

```bash
ittup
```

!!! note "Messaggi rossi al primo avvio?"
    È normale: il bot ti sta avvisando che non è ancora configurato. Al primo avvio crea la cartella di configurazione e il file `ittup.json`. Prosegui con la [Configurazione](../config/intro.md).
