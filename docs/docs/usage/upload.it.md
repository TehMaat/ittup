# Upload base

I tre flag fondamentali: `-u`, `-f`, `-scan`. Tutti portano a termine l'intero processo — analisi, screenshot, ricerca metadata, creazione `.torrent`, upload sul tracker, seeding nel client.

## `-u` — un singolo file

```bash
ittup -u "/home/ITT/upload/film.mkv"
```

Carica **un file**. Il bot lo analizza, ricava titolo e tag dal nome, crea il torrent.

## `-f` — una cartella

```bash
ittup -f "/home/ITT/upload/nomecartella"
```

Crea **un unico torrent con il contenuto della cartella**, che prende il nome della cartella. Dentro può esserci un film o una serie: per il bot non fa differenza.

Usalo per: stagioni complete, film in più parti, contenuti con file di accompagnamento.

Nel torrent vanno solo i file che stanno direttamente nella cartella. Una serie con una cartella per stagione (`Serie/Serie.S01…/`, `Serie/Serie.S02…/`) e nessun video suo si ferma con un errore: carica una stagione alla volta con `-f`, o tutta la serie con `-scan`.

## `-scan` — tutto il contenuto di un percorso

```bash
ittup -scan "/home/ITT/upload"
```

È `-u` e `-f` insieme: analizza **ogni file e ogni cartella** dentro il percorso (ricorsivamente) e processa tutto, un torrent per ogni elemento trovato. Gli elementi vengono caricati in ordine alfanumerico (`E2` prima di `E10`).

Una serie con una cartella per stagione e nessun video suo viene divisa nelle sue stagioni: un season pack per ogni cartella con la stagione nel nome (`Serie.S01…`, `Serie.S02…`), anche quando fai lo scan della cartella che contiene la serie. Ogni pack prende la stagione della sua cartella, anche dentro una cartella chiamata `Serie.S01-S02`.

!!! tip "Quanti contenuti alla volta?"
    Su cartelle molto grandi puoi limitare il numero di elementi processati con `FAST_LOAD` nelle [Opzioni avanzate](../config/options.md).

## Modificatori

Si combinano con `-u`, `-f` e `-scan`:

| Flag | Effetto |
|---|---|
| `-noup` | Crea solo il `.torrent` (nell'[archivio](../config/options.md#percorsi)), **niente upload** né seeding |
| `-noseed` | Upload sul tracker **senza seeding**: il torrent non viene consegnato al client |
| `-dup` | Controlla i [duplicati](../config/options.md#duplicati) sul tracker prima di caricare |
| `-personal` | Marca l'upload come **personal release** |
| `-fl25` `-fl50` `-fl75` `-fl100` | Carica in **freeleech** 25, 50, 75 o 100% (`--freeleech25`…). Il tracker lo applica solo se il tuo account può impostare il freeleech |
| `-int` | Carica come **release internal** (`--internal`) |
| `-mod` | Chiede al tracker di **moderare** l'upload (`--moderation`): il torrent aspetta l'approvazione dello staff |
| `-force <categoria>` | Forza la categoria: `movie`, `tv`, `game`, `edicola` (senza argomento: `movie`) |
| `-notitle "<titolo>"` | Usa questo titolo per la ricerca su TMDB invece di quello ricavato dal nome del file |
| `-reseed` | Modalità reseed ([Reseed](reseed.md)) |

!!! note "`-int` e il freeleech richiedono il permesso"
    Il tracker applica `-int` e `-fl25`…`-fl100` solo allo staff e ai membri di un gruppo internal: per gli altri account carica il torrent senza, e senza errori. Dopo l'upload il bot rilegge il torrent e ti avvisa se non sono stati applicati.

## Moderazione

Quando il MediaInfo dice che un file potrebbe non essere quello che dice il nome, il bot lo carica comunque ma chiede al tracker di **moderarlo**, anche se il tuo account è trusted: uno staffer lo controlla prima che vada online. Oggi succede per un **possibile falso REMUX**, un REMUX con la traccia video ricodificata con x264/x265. Il log dice il motivo:

```
<> Warning: possible fake REMUX, the video track was encoded with 'x264 core 164 ...'
Sent to moderation: possible fake REMUX: video encoded with x264 core 164 ...
```

Il titolo, il tipo e la descrizione non cambiano: è lo staff a correggere, approvare o rifiutare il torrent. Gli altri avvisi (formato HDR sconosciuto, PQ10, HYBRID) non mandano l'upload in moderazione. Se il tuo account non è trusted, ogni upload va già in moderazione.

Con `"AUTO_MODERATION": "False"` nelle [Opzioni avanzate](../config/options.md) il bot mostra solo l'avviso, come prima. `-mod` chiede sempre la moderazione.

## Caratteri rifiutati dal tracker

Il tracker rifiuta i torrent con file o cartelle che hanno `:` `?` `*` `<` `>` `|` `"` `\` nel nome, o che finiscono con un punto o uno spazio. Prima di creare il torrent il bot **li rinomina su disco** e scrive ogni rinomina nel log: `Titolo: Sub` diventa `Titolo - Sub`, gli altri caratteri vengono tolti. Trattini, punti esclamativi e gli altri caratteri restano.

!!! warning "File in seed altrove"
    Un file rinominato non viene più trovato dai client che lo stavano già seedando con il vecchio nome.

## ID nel nome

Se il nome del file o della cartella contiene un ID, il bot lo usa invece di cercare il titolo su TMDB:

```text
Matrix (1999) {imdb-tt0133093}.mkv
Matrix (1999) {tmdb-603}.mkv
Matrix (1999) [tmdbid-603].mkv
Matrix (1999) (tmdb-603).mkv
Matrix.1999.tt0133093.1080p.mkv
```

Il formato `{imdb-tt…}` è quello di Radarr, Sonarr e Plex, `[tmdbid-…]` quello di Jellyfin; vanno bene anche le parentesi tonde, `=` al posto del trattino (Emby) e l'ID IMDB da solo (`tt0133093`). Con il solo ID IMDB il bot chiede a TMDB l'ID TMDB corrispondente; con il solo ID TMDB ricava l'ID IMDB da TMDB. Entrambi vengono inviati al tracker. Il tag viene tolto dal titolo mostrato sul tracker.

Senza ID, il bot cerca su TMDB il titolo ricavato dal nome. Se non lo trova riprova con il nome completo prima dell'anno (`(500) Days of Summer`) e con i titoli tra parentesi (`Lo Chiamavano Jeeg Robot (They Call Me Jeeg)`), e infine con una tolleranza sull'anno: un anno di differenza per i film (uscite a fine anno), l'anno di una stagione successiva per le serie.

## Titoli non trovati su TMDB

Quando TMDB non trova il titolo, il bot chiede l'ID TMDB (`0` salta). L'ID inserito viene salvato in `ittup_config/manual_ids.json`, così al prossimo caricamento dello stesso titolo non viene chiesto di nuovo: gli altri episodi della stessa serie, o lo stesso film caricato più tardi. Nel log il bot scrive `TMDB ID … from the IDs typed in a previous upload`.

- Un film deve avere lo stesso titolo e lo stesso anno; una serie va bene anche quando il nome dell'episodio non ha l'anno.
- Con `SKIP_TMDB` il bot non chiede, ma usa comunque gli ID salvati prima.
- Un ID nel nome del file ha la precedenza su quello salvato. Lo skip (`0`) non viene salvato.
- Hai inserito un ID sbagliato? Togli la sua riga da `manual_ids.json` (o cancella il file). Se il file non si può leggere, il bot lo tiene come `manual_ids.json.bad` e ne crea uno nuovo.

```json
{
    "tv|bake off italia|": {"tmdb_id": 12345, "title": "Bake Off Italia - Dolci in forno", "saved": "2026-11-07"}
}
```

## Esempio completo

```bash
ittup -dup -u "/home/parzival/TEST/scan/007 - Vivi e lascia morire (1973).mkv"
```

Analizza il file, costruisce titolo e tag, controlla i duplicati su ItaTorrents, lo carica e avvia il seeding.

!!! note "Cosa vedi a schermo"
    Il bot mostra una tabella dei file in lavorazione, poi per ogni contenuto: ricerca TMDB, estrazione screenshot, upload immagini, creazione torrent, risposta del tracker, invio al client. La guida [Primo upload passo-passo](../guides/first-upload.md) descrive ogni fase.
