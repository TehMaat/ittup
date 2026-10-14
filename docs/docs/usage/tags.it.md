# Tag e titoli

Il titolo del torrent è composto dal **titolo del media** più una serie di **tag** ricavati dall'analisi del file: risoluzione, sorgente, codec audio/video, lingua, HDR…

Tag generabili: `version`, `resolution`, `uhd`, `platform`, `source`, `remux`, `multi`, `acodec`, `channels`, `flag`, `subtitle`, `vcodec`, `hdr`.

`video_encoder` è ancora accettato in `TAGS_POSITION_*` e in `ban_list.json`, così le configurazioni esistenti continuano a funzionare, ma non aggiunge più nulla: l'encoder fa parte di `vcodec`.

## Come viene costruito il titolo

Per ogni film e serie il bot **costruisce da zero** titolo e tag a partire dall'analisi tecnica del media (MediaInfo) e dal nome del file, nell'ordine definito da `TAGS_POSITION_MOVIE` / `TAGS_POSITION_SERIE` ([Opzioni avanzate](../config/options.md#posizione-dei-tag-nel-titolo)). Succede a ogni upload: non c'è un flag da attivare (il vecchio flag `-b` di Unit3Dup non esiste più).

Quando TMDB trova il film o la serie, il titolo è il **titolo italiano di TMDB**, con la sua punteggiatura (`Spider-Man: No Way Home`), anche quando il nome del file è in inglese. Senza traduzione italiana, o se la ricerca su TMDB viene saltata, il titolo viene dal nome.

Il titolo ricavato dal nome mantiene i caratteri speciali scritti nel nome: `Spider-Man.No.Way.Home.2021` diventa `Spider-Man No Way Home`, `Mission: Impossible - Dead Reckoning (2023)` mantiene i due punti e il trattino.

## Pack di stagioni ed episodi

Un pack di stagione si scrive `S04`, un pack di episodi `S04E01-06`, anche quando nel nome c'è uno spazio o un punto tra stagione ed episodi (`S04 E01-06`, `S04.E01-06`). Sul tracker entrambi hanno numero episodio `0` (pack). Quando il pack contiene tutti gli episodi di una stagione conclusa su TMDB (`S04E01-10` di una stagione da 10 episodi), il titolo riporta solo `S04`.

**Non rinomina il tuo file**: costruisce solo il titolo del torrent mostrato sulla pagina del tracker.

## Codec video

La famiglia del codec (264, 265 o altro) viene letta dal nome del file (`x264`, `x265`, `H264`, `H.265`, `AVC`, `HEVC`…) o, se manca, dal MediaInfo. Se i due non concordano vince il MediaInfo e il bot mostra un avviso.

Il tipo di release, letto dai tag source/remux del nome del file, decide come si scrive il codec:

| Tipo di release | Tag | Codec |
|---|---|---|
| Untouched | `REMUX`, `BDREMUX`, `BDMUX`, `VU`, `UNTOUCHED`, `DVDMUX`, `FULL DISC` | `AVC` / `HEVC` |
| WEB-DL | `WEB-DL`, `WEB`, `WEBDL`, `WEB-DLMUX`, `WEBMUX`, `DLMUX`, `HDTV` | `H.264` / `H.265` |
| Encode | `ENCODE`, `WEBRIP`, `BDRIP`, `BRRIP`, `DVDRIP`, `UHDRIP`, `FHDRIP`, `WEB-DLRIP` | `x264` / `x265` |

Con `BLURAY` da solo, o senza tipo di release nel nome, il bot guarda l'encoder scritto nel MediaInfo: `x264` / `x265` se trova la firma x264/x265, altrimenti `H.264` / `H.265`. Su una release untouched la firma x264/x265 mostra solo un avviso di "possibile falso REMUX". Gli altri codec (AV1, VP9, VC-1, MPEG-2, XviD…) vengono scritti così come sono.

## Sorgente e tipo sul tracker

La sorgente scritta nel nome (`WEB-DL`, `WEBRip`, `REMUX`, `DLMux`…) decide anche il **tipo** del torrent sul tracker: vince su codec e tag generici scritti prima (`HEVC`, `FullHD`, `BluRay`), quindi `Film.2020.1080p.HEVC.WEB-DL` è un WEB-DL e `Film.2020.1080p.BluRay.REMUX` un Remux. Il bot guarda prima il nome della cartella, poi quello del file video. Senza sorgente nel nome, un codec (`x264`, `HEVC`…) vale Encode.

I rip delle piattaforme streaming vengono divisi in piattaforma e sorgente: `NFRip` diventa `NF WEBRip` (vale per tutte le piattaforme di `tags_list.json`, es. `AMZNRip` → `AMZN WEBRip`).

## Codec audio

Il titolo tiene al massimo due codec audio: il **miglior codec ITA** e il **miglior codec nella lingua originale** del film o della serie (letta da TMDB, inglese se TMDB non la conosce). Se resta posto, viene riempito con le migliori tracce senza lingua. Codec dal migliore: `TrueHD`, `DTS-HD MA`, `FLAC`, `PCM`, `DTS-ES`, `DTS`, `DD+`, `DD`, `AAC`, `HE-AAC`, `Opus`, `MPEG`. A parità di codec vincono Atmos e poi più canali. Lo stesso codec viene scritto una volta sola.

Dopo i codec vengono le lingue: `ITA`, la lingua originale, poi le altre lingue del file, che hanno solo la bandiera e nessun codec. Esempio con tracce italiana, inglese e giapponese di un film giapponese: `DD 5.1 DTS-HD MA 5.1 ITA JPN ENG`.

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

Esempio — mai includere il codec video nel titolo:

```json
{
    "vcodec": "banned"
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
