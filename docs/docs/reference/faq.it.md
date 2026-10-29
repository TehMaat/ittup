# FAQ / Troubleshooting

## Primo avvio e configurazione

### Messaggi rossi al primo avvio

Normale: il bot ha appena creato `ittup.json` e i file di supporto con i valori segnaposto, e ti avvisa che mancano le chiavi. Segui i [Primi passi](../config/intro.md).

### `-> Please Fix 'CAMPO' ['valore'] in settings.json`

Un valore in `ittup.json` è malformato (colore inesistente, numero non numerico, URL senza schema…). Apri il file e correggi il campo indicato tra apici. La [Config completa](config.md) elenca tipo e valori ammessi di ogni chiave.

### `'-mt' has been removed: ITTup uploads only to ItaTorrents`

`-mt` e `-tracker` arrivano da Unit3Dup e non esistono più: ogni upload va su ItaTorrents. Togli il flag dal comando o dallo script.

### `-> No PID value for ITT_PID`

`ITT_PID` contiene ancora un segnaposto: inserisci la tua passkey ITT. Vedi [Tracker](../config/trackers.md).

## Client torrent

### `Unknown Torrent Client name 'xxx'`

`TORRENT_CLIENT` deve essere esattamente `qbittorrent`, `transmission` o `rtorrent`. Vedi [Client torrent](../config/clients.md).

### Il bot non si connette al client

- WebUI attiva? (qBittorrent: *Strumenti → Opzioni → WebUI*)
- Host e porta giusti? (`QBIT_HOST`/`QBIT_PORT` e equivalenti)
- Credenziali corrette?
- Il client gira su un'altra macchina/container? Allora serve anche `SHARED_*_PATH` ([dettagli](../config/clients.md#shared__path-client-su-unaltra-macchina))

### Upload senza client?

Sì: `-noseed` carica senza seeding, `-noup` crea solo il `.torrent`. Differenza: con `-noseed` il torrent **arriva sul tracker**, con `-noup` no — resta solo nell'archivio locale.

## Dipendenze

### `ffmpeg` non trovato

FFmpeg non è nel PATH. [Windows](../install/windows.md#1-installa-ffmpeg) · [Linux](../install/linux.md): `sudo apt install ffmpeg`. Dopo averlo aggiunto al PATH, chiudi e riapri il terminale.

### `[FFMPEG-ffprobe too old]`

Il controllo dei file corrotti (`CHECK_CORRUPTED`) richiede ffprobe 5.1 o successivo. Su Ubuntu 22.04 `apt` installa la 4.4: [installa una build statica](../install/linux.md#1-installa-le-dipendenze), oppure imposta `CHECK_CORRUPTED` a `False`.

### `pdftocairo` non riconosciuto

Poppler manca o non è nel PATH — serve solo per i PDF. [Windows](../install/windows.md#2-poppler-solo-per-i-pdf) · Linux: `sudo apt install poppler-utils`.

## Upload

### `There are no Media to process`

Nel percorso non c'è niente che il bot riconosca come media, oppure il percorso è sbagliato o senza permessi di lettura.

### `Invalid -force category`

Le categorie valide per `-force` sono: `movie`, `tv`, `game`, `edicola`.

### `Skipping game upload, no IGDB credentials provided`

Mancano `IGDB_CLIENT_ID` / `IGDB_ID_SECRET`: i giochi vengono saltati, il resto prosegue. Vedi [Giochi](../guides/games.md).

### Il titolo viene riconosciuto male

Usa `-notitle "Titolo Corretto"` per forzare la ricerca TMDB, `-tag` per scegliere il release group e `TAGS_POSITION_*` per scegliere i tag. Vedi [Tag e titoli](../usage/tags.md).

### `-int` o `-fl100` non vengono applicati

Il tracker li accetta solo dallo staff e dai membri di un gruppo internal: per gli altri account carica il torrent senza, e senza errori. Dopo l'upload il bot rilegge il torrent e lo segnala con un avviso `-int: ...` o `-fl100: ...`. Vedi [Upload base](../usage/upload.md).

### Il controllo duplicati non trova un torrent che è già sul tracker

Il bot cerca per titolo e, per film e serie, per TMDB ID: controlla nel log `Duplicate check: N torrents on the tracker for '...'`. Un torrent con un'altra risoluzione o di un'altra categoria non è un duplicato, e uno con una dimensione fuori da `SIZE_TH` nemmeno. Vedi [Duplicati](../config/options.md#duplicati).

### Dove finiscono i `.torrent` creati?

In `TORRENT_ARCHIVE_PATH`, nella sottocartella `ITT`: `<archivio>/ITT/nome.torrent`. Default: `ittup_config/torrent_archive_path/`.

## Watcher

### `Watcher path does not exist or is not configured`

`WATCHER_PATH` non esiste o è rimasto `no_path`. Configura entrambi i percorsi del watcher ([dettagli](../usage/watcher.md)).

### Un file è finito in `watcher_quarantine_path`

L'upload è fallito per un motivo che non si risolve da solo (file corrotto, upload rifiutato dal tracker…) oppure è fallito ancora dopo `WATCHER_MAX_RETRIES` tentativi. Il motivo è nel file `<nome>.error.txt` accanto. Sistemato il problema, rimetti il file in `WATCHER_PATH` o caricalo con `-u`. Vedi [Quarantena](../usage/watcher.md#quarantena).

### `Retry 1/5 in 60 seconds`

Un errore temporaneo (rete, tracker offline, rate limit): il watcher riprova da solo con un'attesa che raddoppia a ogni tentativo, e intanto carica gli altri file. Vedi [Coda persistente e nuovi tentativi](../usage/watcher.md#coda-persistente-e-nuovi-tentativi).

## Altro

### Il bot funziona su seedbox senza sudo?

Sì, con uv, che porta anche un Python con sqlite3 già incluso: guida [Seedbox ultra.cc](../install/seedbox.md).

### Come aggiorno?

`pip install ittup --upgrade` — [Aggiornamento](../install/upgrade.md).

### Dove chiedo aiuto?

Sul [Discord](https://discord.gg/VMYaVzq2AF) o aprendo una [issue su GitHub](https://github.com/TehMaat/ittup/issues).
