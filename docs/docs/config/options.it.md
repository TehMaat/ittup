# Opzioni avanzate

Sezione `user_preferences` di `ittup.json` (più `console_options` in fondo). Nessuna di queste opzioni è obbligatoria: i default vanno bene per iniziare.

## Screenshot

```json
"NUMBER_OF_SCREENSHOTS": 4,
"COMPRESS_SCSHOT": 3,
"RESIZE_SCSHOT": "False",
"WEBP_ENABLED": "False",
```

| Chiave | Effetto |
|---|---|
| `NUMBER_OF_SCREENSHOTS` | Quanti screenshot estrarre dal video |
| `COMPRESS_SCSHOT` | Livello di compressione delle immagini |
| `RESIZE_SCSHOT` | Ridimensiona gli screenshot prima dell'upload |
| `WEBP_ENABLED` | Aggiunge una webp animata alla descrizione del torrent |

Gli screenshot vengono presi a intervalli regolari tra il 10% e il 90% del video. Un frame troppo scuro viene sostituito con uno più luminoso lì vicino. I video HDR (HDR10, HDR10+, HLG, Dolby Vision con base layer HDR10) vengono convertiti in SDR con il tone mapping, così i colori non risultano slavati: serve un ffmpeg con il filtro `zscale` (libzimg), presente nelle build più comuni.

## Duplicati

```json
"DUPLICATE_ON": "true",
"SKIP_DUPLICATE": "false",
"SIZE_TH": 10,
```

| Chiave | Effetto |
|---|---|
| `DUPLICATE_ON` | Attiva il controllo duplicati prima dell'upload (equivale al flag `-dup`) |
| `SKIP_DUPLICATE` | Salta il contenuto se viene trovato un duplicato, senza chiedere |
| `SIZE_TH` | Soglia percentuale: un torrent sul tracker è considerato "stesso contenuto" se la differenza di dimensione rispetto al tuo file è entro questa percentuale |

## Cache

```json
"CACHE_PATH": "no_path",
"CACHE_SCR": "False",
"CACHE_DBONLINE": "False",
"TMDB_DEBUG": "False",
```

| Chiave | Effetto |
|---|---|
| `CACHE_PATH` | Cartella della cache (default: `ittup_config/cache_path`) |
| `CACHE_SCR` | Riusa gli screenshot già estratti |
| `CACHE_DBONLINE` | Mette in cache i risultati di TMDB e delle ricerche online |
| `TMDB_DEBUG` | Mostra nel log i punteggi di confronto dei titoli TMDB (titolo, originale, titoli alternativi, traduzioni). Fa richieste HTTP extra: lascialo spento se non stai indagando un match sbagliato |

## Lingua, anonimato e firma

```json
"PREFERRED_LANG": "all",
"ANON": "False",
"PERSONAL_RELEASE": "False",
"RELEASER_SIGN": "",
"TORRENT_COMMENT": "no_comment",
```

| Chiave | Effetto |
|---|---|
| `PREFERRED_LANG` | Codice lingua preferita (ISO 3166, es. `it`) o `all`: il bot avvisa se l'audio non corrisponde |
| `ANON` | Upload **anonimo**: il tuo username non compare sulla pagina del torrent |
| `PERSONAL_RELEASE` | Marca ogni upload come personal release (equivale al flag `-personal`) |
| `RELEASER_SIGN` | La tua firma da releaser, aggiunta al titolo (max 20 caratteri; vedi [Tag e titoli](../usage/tags.md)) |
| `TORRENT_COMMENT` | Commento inserito nel file `.torrent` |

## Posizione dei tag nel titolo

```json
"TAGS_POSITION_MOVIE": ["title", "year", "part", "version", "resolution", "uhd", "platform", "source", "remux", "multi", "acodec", "channels", "flag", "subtitle", "hdr", "vcodec"],
"TAGS_POSITION_SERIE": ["title", "season", "version", "resolution", "uhd", "platform", "source", "remux", "multi", "acodec", "channels", "flag", "subtitle", "hdr", "vcodec"],
```

L'**ordine** con cui i tag compongono il titolo del torrent, per film e serie. Puoi riordinare o togliere voci (minimo 5); i nomi devono restare tra quelli ammessi. Dettagli: [Tag e titoli](../usage/tags.md).

## Rinomina i file come il titolo

```json
"RENAME_FILES": "False",
```

Con `True` il bot **rinomina su disco i file originali** come il titolo mostrato sul tracker, con i punti al posto degli spazi, prima di creare il torrent: `film.2021.1080p.web-dl.mkv` diventa `Spider-Man.No.Way.Home.2021.1080p.WEB-DL.DD+.5.1.ITA.ENG.H.264.mkv`. Vale per `-u`, `-f`, `-scan` e `-watcher`, per film e serie.

Per una cartella, la cartella prende il titolo; lo prende anche il file video di una cartella con un film, e in un pack di stagione ogni episodio prende il titolo con il suo `SxxExx`. Una cartella con più film mantiene i nomi dei file. I caratteri non validi nel nome di un file (`:` `?` `*`…) vengono tolti.

!!! warning "File in seed altrove"
    Un file rinominato non viene più trovato dai client che lo stavano già seedando con il vecchio nome.

## Watcher

```json
"WATCHER_INTERVAL": 60,
"WATCHER_TIMEOUT": 3600,
"WATCHER_PATH": "no_path",
"WATCHER_DESTINATION_PATH": "no_path",
```

| Chiave | Effetto |
|---|---|
| `WATCHER_INTERVAL` | Ogni quanti **secondi** il watcher controlla la cartella |
| `WATCHER_TIMEOUT` | **Secondi** massimi per processare un singolo file o cartella: se è ancora in corso viene fermato e saltato. `0` = nessun limite |
| `WATCHER_PATH` | Cartella monitorata (es. dove scarica il tuo client) |
| `WATCHER_DESTINATION_PATH` | Cartella dove i file vengono spostati e poi caricati |

Come funziona: [Watcher](../usage/watcher.md).

## Percorsi

```json
"TORRENT_ARCHIVE_PATH": "no_path",
```

Cartella dove il bot archivia i `.torrent` generati, dentro la sottocartella `ITT` (`<archivio>/ITT/...`). Con `no_path` usa il default dentro `ittup_config`.

## YouTube

```json
"YOUTUBE_PREF_LANG": "IT",
"SKIP_YOUTUBE": "true",
"SKIP_TMDB": "false",
```

| Chiave | Effetto |
|---|---|
| `YOUTUBE_PREF_LANG` | Codice paese/lingua (ISO 3166, es. `IT`) usato per cercare i trailer su YouTube |
| `SKIP_YOUTUBE` | Salta del tutto la ricerca trailer su YouTube |
| `SKIP_TMDB` | Salta l'interrogazione di TMDB (sconsigliato per i video) |

## FAST_LOAD

```json
"FAST_LOAD": "0",
```

Limita il numero di contenuti processati per ogni esecuzione (valori utili: 1–150; `0` = nessun limite). Comodo per testare uno `-scan` su una cartella enorme senza processarla tutta.

## Colori della console (`console_options`)

```json
"console_options": {
    "NORMAL_COLOR": "blue bold",
    "ERROR_COLOR": "red bold",
    "WELCOME_MESSAGE": "https://itatorrents.xyz",
    "WELCOME_MESSAGE_COLOR": "blue",
    "WELCOME_MESSAGE_BORDER_COLOR": "yellow",
    "PANEL_MESSAGE_COLOR": "blue",
    "PANEL_MESSAGE_BORDER_COLOR": "yellow",
    "QUESTION_MESSAGE_COLOR": "yellow"
}
```

Personalizza testo e colori dell'output. Colori ammessi: `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`, anche in variante `bold` (es. `"cyan bold"`).
