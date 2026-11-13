# Giochi

Per i giochi il bot interroga **IGDB** (Internet Game Database) e trasmette al tracker l'ID del titolo, come fa con TMDB per i film.

## 1. Crea le credenziali IGDB

IGDB appartiene a Twitch: le API si attivano dalla console sviluppatori Twitch.

1. Account su [twitch.tv](https://www.twitch.tv) (con 2FA attiva)
2. Vai su [dev.twitch.tv/console](https://dev.twitch.tv/console) → *Applications* → *Register Your Application*
3. Nome a piacere, OAuth Redirect URL `http://localhost`, categoria *Application Integration*
4. Ottieni **Client ID** e genera il **Client Secret**

## 2. Configura il bot

In `tracker_config` di `ittup.json`:

```json
"IGDB_CLIENT_ID": "il_tuo_client_id",
"IGDB_ID_SECRET": "il_tuo_client_secret",
```

!!! warning "Senza credenziali i giochi vengono saltati"
    Con `IGDB_CLIENT_ID` a `no_key` il bot mostra `Skipping game upload, no IGDB credentials provided` e prosegue solo con gli altri contenuti.

## 3. Upload

```bash
ittup -f "/percorso/Nome.Gioco.v1.0.REPACK"
ittup -force game -f "/percorso/cartella_gioco"
```

Il bot crea un **oggetto Game**: cerca il titolo su IGDB, ricava l'ID (`igdb`) e riconosce la **piattaforma** (PC, console…) per il tag corrispondente. Le altre proprietà (`name`, `category_id`, `description`…) funzionano [come per i video](../index.md#oggetto-game), con `tmdb` a valore neutro.

!!! tip "Categoria non riconosciuta?"
    Se il bot scambia il gioco per un film, forza la categoria con `-force game`.

## 4. Descrizione

La descrizione del torrent è costruita da IGDB, a sezioni:

1. la copertina, centrata;
2. titolo e anno di uscita;
3. una tabella con piattaforme, genere, sviluppatore, publisher, data di uscita e modalità di gioco (una riga senza dato non compare);
4. la descrizione (il `summary` di IGDB);
5. fino a 4 screenshot;
6. il trailer, dentro uno spoiler: il primo video con "trailer" nel nome, altrimenti il primo video;
7. il link alla pagina IGDB.

Copertina e screenshot vengono scaricati da IGDB e ricaricati sugli [image host](../config/imagehosts.md) con chiave, con lo stesso ordine di priorità degli screenshot dei video. Sono decorativi: senza chiave di un image host, o quando un'immagine fallisce, la descrizione resta senza e l'upload prosegue, anche con `SCREENSHOTS_QUORUM` attivo.
