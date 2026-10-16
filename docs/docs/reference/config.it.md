# Config completa

Ogni chiave di `ittup.json`, sezione per sezione. "Default" è il valore nel file generato al primo avvio; i segnaposto `no_key` / `no_pass` / `no_path` significano "non configurato".

## `tracker_config`

| Chiave | Tipo | Default | Obbligatoria | Descrizione |
|---|---|---|---|---|
| `ITT_URL` | stringa | `https://itatorrents.xyz` | sì | URL del tracker ITT |
| `ITT_APIKEY` | stringa | `no_key` | sì | API key del tuo profilo ITT |
| `ITT_PID` | stringa | `no_key` | sì | Passkey ITT (usata nell'announce URL) |
| `TMDB_APIKEY` | stringa | `no_key` | per i video | Chiave TheMovieDB |
| `TVDB_APIKEY` | stringa | `no_key` | consigliata per le serie | Chiave TheTVDB |
| `IMGBB_KEY` | stringa | `no_key` | almeno un host | Chiave ImgBB |
| `FREE_IMAGE_KEY` | stringa | `no_key` | almeno un host | Chiave FreeImage |
| `LENSDUMP_KEY` | stringa | `no_key` | almeno un host | Chiave LensDump |
| `PTSCREENS_KEY` | stringa | `no_key` | almeno un host | Chiave PtScreens |
| `IMGFI_KEY` | stringa | `no_key` | almeno un host | Chiave ImgFI |
| `PASSIMA_KEY` | stringa | `no_key` | almeno un host | Chiave PassIMA |
| `IMARIDE_KEY` | stringa | `no_key` | almeno un host | Chiave ImaRide |
| `YOUTUBE_KEY` | stringa | `no_key` | no | Chiave YouTube Data API (trailer) |
| `IGDB_CLIENT_ID` | stringa | `no_key` | per i giochi | Client ID IGDB/Twitch |
| `IGDB_ID_SECRET` | stringa | `no_key` | per i giochi | Client Secret IGDB/Twitch |

## `torrent_client_config`

| Chiave | Tipo | Default | Obbligatoria | Descrizione |
|---|---|---|---|---|
| `QBIT_USER` | stringa | `admin` | se usi qBittorrent | Username WebUI |
| `QBIT_PASS` | stringa | `no_pass` | se usi qBittorrent | Password WebUI |
| `QBIT_HOST` | stringa | `127.0.0.1` | se usi qBittorrent | Host del client |
| `QBIT_PORT` | numero | `8080` | se usi qBittorrent | Porta WebUI |
| `SHARED_QBIT_PATH` | stringa | `no_path` | no | Percorso visto dal client se gira altrove |
| `QBIT_SKIP_CHECK` | booleano | `True` | no | Salta il controllo hash all'aggiunta del torrent |
| `QBIT_ENABLED` | booleano | `True` | no | `False` disattiva qBittorrent: nessuna connessione, niente seeding |
| `TRASM_USER` | stringa | `admin` | se usi Transmission | Username |
| `TRASM_PASS` | stringa | `no_pass` | se usi Transmission | Password |
| `TRASM_HOST` | stringa | `127.0.0.1` | se usi Transmission | Host |
| `TRASM_PORT` | numero | `9091` | se usi Transmission | Porta |
| `SHARED_TRASM_PATH` | stringa | `no_path` | no | Percorso visto dal client se gira altrove |
| `RTORR_USER` | stringa | `admin` | se usi rTorrent | Username |
| `RTORR_PASS` | stringa | `no_pass` | se usi rTorrent | Password |
| `RTORR_HOST` | stringa | `127.0.0.1` | se usi rTorrent | Host |
| `RTORR_PORT` | numero | `9091` | se usi rTorrent | Porta |
| `SHARED_RTORR_PATH` | stringa | `no_path` | no | Percorso visto dal client se gira altrove |
| `TORRENT_CLIENT` | stringa | `qbittorrent` | per upload con seeding | `qbittorrent`, `transmission` o `rtorrent` |
| `TAG` | stringa | `ADDED TORRENTS` | no | Etichetta applicata ai torrent nel client |

## `user_preferences`

| Chiave | Tipo | Default | Descrizione |
|---|---|---|---|
| `PTSCREENS_PRIORITY` | numero | `0` | Priorità host immagini (0 = primo) |
| `LENSDUMP_PRIORITY` | numero | `1` | Priorità LensDump |
| `FREE_IMAGE_PRIORITY` | numero | `2` | Priorità FreeImage |
| `IMGBB_PRIORITY` | numero | `3` | Priorità ImgBB |
| `IMGFI_PRIORITY` | numero | `4` | Priorità ImgFI |
| `PASSIMA_PRIORITY` | numero | `5` | Priorità PassIMA |
| `IMARIDE_PRIORITY` | numero | `6` | Priorità ImaRide |
| `NUMBER_OF_SCREENSHOTS` | numero | `4` | Screenshot estratti dal video (2–10) |
| `TAGS_POSITION_MOVIE` | lista | vedi [Opzioni](../config/options.md#posizione-dei-tag-nel-titolo) | Ordine dei tag nei titoli dei film (5–17 voci) |
| `TAGS_POSITION_SERIE` | lista | vedi [Opzioni](../config/options.md#posizione-dei-tag-nel-titolo) | Ordine dei tag nei titoli delle serie |
| `YOUTUBE_PREF_LANG` | stringa | `IT` | Codice paese/lingua (ISO 3166) per la ricerca trailer su YouTube |
| `DUPLICATE_ON` | booleano | `true` | Controllo duplicati a ogni upload |
| `SKIP_DUPLICATE` | booleano | `false` | Salta i contenuti duplicati senza chiedere |
| `SKIP_TMDB` | booleano | `false` | Non interrogare TMDB |
| `SKIP_YOUTUBE` | booleano | `true` | Non cercare trailer su YouTube |
| `SIZE_TH` | numero | `10` | Soglia % di differenza dimensione per il match duplicati |
| `WATCHER_INTERVAL` | numero | `60` | Secondi tra i controlli del watcher |
| `WATCHER_TIMEOUT` | numero | `3600` | Secondi massimi che il watcher dedica a un file o cartella prima di saltarlo (`0` = nessun limite) |
| `WATCHER_PATH` | stringa | `no_path` | Cartella monitorata dal watcher |
| `WATCHER_DESTINATION_PATH` | stringa | `no_path` | Destinazione dei file del watcher |
| `WATCHER_QUARANTINE_PATH` | stringa | `no_path` | Cartella degli upload falliti del watcher |
| `WATCHER_MAX_RETRIES` | numero | `5` | Nuovi tentativi di un upload fermato da un errore temporaneo |
| `TORRENT_ARCHIVE_PATH` | stringa | `no_path` | Archivio dei `.torrent` generati |
| `CACHE_PATH` | stringa | `no_path` | Cartella cache |
| `COMPRESS_SCSHOT` | numero | `3` | Compressione screenshot |
| `RESIZE_SCSHOT` | booleano | `False` | Ridimensiona gli screenshot |
| `TIMEOUT_SCSHOT` | numero | `120` | Secondi massimi per un singolo screenshot (`0` = nessun limite) |
| `TORRENT_COMMENT` | stringa | `no_comment` | Commento nel file `.torrent` |
| `PREFERRED_LANG` | stringa | `all` | Lingua preferita (ISO 3166) o `all` |
| `ANON` | booleano | `False` | Upload anonimo |
| `WEBP_ENABLED` | booleano | `False` | Webp animata nella descrizione |
| `CACHE_SCR` | booleano | `False` | Cache degli screenshot |
| `CACHE_DBONLINE` | booleano | `False` | Cache su disco delle ricerche online (ID TMDB/IMDB/TVDB/IGDB) |
| `TMDB_DEBUG` | booleano | `False` | Log dei punteggi di confronto titoli TMDB (richieste HTTP extra) |
| `PERSONAL_RELEASE` | booleano | `False` | Personal release su ogni upload |
| `RENAME_FILES` | booleano | `False` | Rinomina i file originali come il titolo del tracker prima dell'upload |
| `CHECK_CORRUPTED` | booleano | `True` | Salta i file video corrotti, controllati con ffprobe (5.1 o successivo) prima dell'upload |
| `CHECK_CORRUPTED_START` | numero | `10` | Inizio dell'intervallo controllato, in percentuale della durata |
| `CHECK_CORRUPTED_END` | numero | `90` | Fine dell'intervallo controllato, in percentuale della durata |
| `CHECK_CORRUPTED_IGNORE_DV` | booleano | `False` | Gli errori dei metadati RPU Dolby Vision non rendono il file corrotto |
| `FAST_LOAD` | numero | `0` | Limita i contenuti processati (1–150; 0 = tutti) |
| `RELEASER_SIGN` | stringa | vuota | Firma releaser (max 20 caratteri) |

## `options`

| Chiave | Tipo | Default | Descrizione |
|---|---|---|---|
| `FTPX_USER` | stringa | `user` | Username FTP |
| `FTPX_PASS` | stringa | `pass` | Password FTP |
| `FTPX_IP` | stringa | `127.0.0.1` | IP del server FTP |
| `FTPX_PORT` | numero | `2121` | Porta FTP |
| `FTPX_LOCAL_PATH` | stringa | `.` | Cartella locale di download |
| `FTPX_ROOT` | stringa | `.` | Cartella remota di partenza |
| `FTPX_KEEP_ALIVE` | booleano | `False` | Mantiene viva la connessione |

## `console_options`

| Chiave | Tipo | Default | Descrizione |
|---|---|---|---|
| `NORMAL_COLOR` | stringa | `blue bold` | Colore messaggi normali |
| `ERROR_COLOR` | stringa | `red bold` | Colore errori |
| `WELCOME_MESSAGE` | stringa | `https://itatorrents.xyz` | Testo del banner di benvenuto |
| `WELCOME_MESSAGE_COLOR` | stringa | `blue` | Colore del banner |
| `WELCOME_MESSAGE_BORDER_COLOR` | stringa | `yellow` | Bordo del banner |
| `PANEL_MESSAGE_COLOR` | stringa | `blue` | Colore dei pannelli |
| `PANEL_MESSAGE_BORDER_COLOR` | stringa | `yellow` | Bordo dei pannelli |
| `QUESTION_MESSAGE_COLOR` | stringa | `yellow` | Colore delle domande |

Colori ammessi: `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white` (+ ` bold`).

I valori booleani accettano `true`/`false`, `1`/`0`, `yes`/`no` (come stringhe o nativi).
