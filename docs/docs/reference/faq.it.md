# FAQ / Troubleshooting

## Primo avvio e configurazione

### Messaggi rossi al primo avvio

Normale: il bot ha appena creato `ittup.json` e i file di supporto con i valori segnaposto, e ti avvisa che mancano le chiavi. Segui i [Primi passi](../config/intro.md).

### `-> Please Fix 'CAMPO' ['valore'] in settings.json`

Un valore in `ittup.json` è malformato (colore inesistente, numero non numerico, URL senza schema…). Apri il file e correggi il campo indicato tra apici. La [Config completa](config.md) elenca tipo e valori ammessi di ogni chiave.

### `'-mt' has been removed: ittup uploads only to ItaTorrents`

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

### `pdftocairo` non riconosciuto

Poppler manca o non è nel PATH — serve solo per i PDF. [Windows](../install/windows.md#2-poppler-solo-per-i-pdf) · Linux: `sudo apt install poppler-utils`.

## Upload

### `There are no Media to process`

Nel percorso non c'è niente che il bot riconosca come media, oppure il percorso è sbagliato o senza permessi di lettura.

### `Invalid -force category`

Le categorie valide per `-force` sono: `movie`, `tv`, `game`, `edicola`.

### `Skipping game upload, no IGDB credentials provided`

Mancano `IGDB_CLIENT_ID` / `IGDB_ID_SECRET`: i giochi vengono saltati, il resto prosegue. Vedi [Giochi](../guides/games.md).

### `User tags file ... not found`

Manca `tags_list.json` nella cartella di configurazione. Viene creato al primo avvio: se l'hai cancellato, rilancia il bot senza argomenti. Vedi [Tag e titoli](../usage/tags.md).

### Il titolo viene riconosciuto male

Usa `-notitle "Titolo Corretto"` per forzare la ricerca TMDB; ritocca `tags_list.json` e `ban_list.json` per correggere i tag. Vedi [Tag e titoli](../usage/tags.md).

### Dove finiscono i `.torrent` creati?

In `TORRENT_ARCHIVE_PATH`, nella sottocartella `ITT`: `<archivio>/ITT/nome.torrent`. Default: `ittup_config/torrent_archive_path/`.

## Watcher

### `Watcher path does not exist or is not configured`

`WATCHER_PATH` non esiste o è rimasto `no_path`. Configura entrambi i percorsi del watcher ([dettagli](../usage/watcher.md)).

## Altro

### Il bot funziona su seedbox senza sudo?

Sì, con pyenv: guida [Seedbox ultra.cc](../install/seedbox.md).

### Come aggiorno?

`pip install --upgrade git+https://github.com/TehMaat/ittup` — [Aggiornamento](../install/upgrade.md).

### Dove chiedo aiuto?

Sul [Discord](https://discord.gg/VMYaVzq2AF) o aprendo una [issue su GitHub](https://github.com/TehMaat/ittup/issues).
