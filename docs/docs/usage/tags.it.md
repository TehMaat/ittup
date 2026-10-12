# Tag e titoli

Il titolo del torrent è composto dal **titolo del media** più una serie di **tag** ricavati dall'analisi del file: risoluzione, sorgente, codec audio/video, lingua, HDR…

Tag generabili: `version`, `resolution`, `uhd`, `platform`, `source`, `remux`, `multi`, `acodec`, `channels`, `flag`, `subtitle`, `vcodec`, `hdr`, `video_encoder`.

## Come viene costruito il titolo

Per ogni film e serie il bot **costruisce da zero** titolo e tag a partire dall'analisi tecnica del media (MediaInfo) e dal nome del file, nell'ordine definito da `TAGS_POSITION_MOVIE` / `TAGS_POSITION_SERIE` ([Opzioni avanzate](../config/options.md#posizione-dei-tag-nel-titolo)). Succede a ogni upload: non c'è un flag da attivare (il vecchio flag `-b` di Unit3Dup non esiste più).

**Non rinomina il tuo file**: costruisce solo il titolo del torrent mostrato sulla pagina del tracker.

## I tre file di personalizzazione

Stanno nella cartella di configurazione (`ittup_config`) e vengono creati al primo avvio con valori di default. Sono JSON modificabili con un editor di testo.

### `tags_list.json` — tag personalizzati

Mappa **parola → tipo di tag**: insegna al bot a riconoscere parole nei nomi dei file e classificarle.

```json
{
    "REMUX": "remux",
    "WEB-DL": "source",
    "AMZN": "platform"
}
```

Usato nella costruzione del titolo: se nel nome del file compare la parola, il valore corrispondente finisce nel tag giusto del titolo. Puoi aggiungere le tue voci (es. sigle di release group o sorgenti particolari).

!!! warning "File richiesto"
    Se `tags_list.json` manca, il bot lo segnala all'avvio.

### `ban_list.json` — tag da escludere dall'autobuild

Esclude interi **tipi di tag** dalla ricostruzione del titolo: un tag elencato qui non finisce mai nel titolo costruito dal bot. Le chiavi sono i nomi dei tag (gli stessi usati in `TAGS_POSITION_*`); il valore è solo un segnaposto.

Esempio — mai includere codec video ed encoder nel titolo:

```json
{
    "vcodec": "banned",
    "video_encoder": "banned"
}
```

### `sign_list.json` — firme releaser

Lista delle firme riconosciute come **release group**. Insieme a `RELEASER_SIGN` ([Opzioni avanzate](../config/options.md#lingua-anonimato-e-firma)) gestisce la firma in coda al titolo (max 20 caratteri, caratteri speciali rimossi).

## Titolo manuale

Quando il nome del file è troppo sporco per ricavarne il titolo (capita con i pack di stagioni senza titolo):

```bash
ittup -u "/percorso/S01.pack.1080p.mkv" -notitle "Nome Della Serie"
```

`-notitle` forza il titolo usato per la **ricerca su TMDB**, senza toccare i tag tecnici.
