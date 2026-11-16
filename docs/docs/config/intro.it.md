# Configurazione — primi passi

## Dove sta la configurazione

Al **primo avvio** il bot crea la cartella `ittup_config` con dentro il file di configurazione principale e i file di supporto:

| Sistema | Percorso |
|---|---|
| Windows | `%LOCALAPPDATA%\ittup_config\` |
| Linux / macOS | `~/ittup_config/` |

Contenuto della cartella:

| File | A cosa serve |
|---|---|
| `ittup.json` | **Configurazione principale**: tracker, api key, client torrent, preferenze |

!!! note "Arrivi da Unit3Dup?"
    Al primo avvio ITTup copia `Unit3Dup_config/Unit3Dbot.json` in `ittup_config/ittup.json` (la vecchia cartella non viene toccata). Dettagli: [Aggiornamento](../install/upgrade.md#arrivi-da-unit3dup).

Nella stessa cartella il bot crea anche le sottocartelle di default `torrent_archive_path` (dove archivia i `.torrent` generati), `cache_path`, `watcher_path`, `watcher_destination_path` e `watcher_quarantine_path` (dove il watcher sposta gli upload falliti) — tutte personalizzabili (vedi [Opzioni avanzate](options.md)). Il watcher salva qui anche la sua coda di upload, `watcher_queue.json`.

## La struttura del file

`ittup.json` è diviso in **cinque sezioni**:

```json
{
    "tracker_config": { },
    "torrent_client_config": { },
    "user_preferences": { },
    "options": { },
    "console_options": { }
}
```

| Sezione | Contenuto | Pagina |
|---|---|---|
| `tracker_config` | URL, api key e passkey di ITT, chiavi TMDB/TVDB/IGDB/YouTube, chiavi image host | [Tracker](trackers.md), [Metadata](metadata.md), [Image host](imagehosts.md) |
| `torrent_client_config` | qBittorrent, Transmission, rTorrent | [Client torrent](clients.md) |
| `user_preferences` | Screenshot, cache, watcher, duplicati, tag, lingua… | [Opzioni avanzate](options.md) |
| `options` | Connessione FTP | [FTP](../usage/ftp.md) |
| `console_options` | Colori e messaggi della console | [Opzioni avanzate](options.md) |

## Configurazione minima

Non serve compilare ogni riga. Per iniziare bastano:

1. **`ITT_APIKEY` + `ITT_PID`** — [Tracker](trackers.md)
2. **`TMDB_APIKEY`** — [Metadata](metadata.md)
3. **Almeno due chiavi image host** — [Image host](imagehosts.md)
4. **`TORRENT_CLIENT` + credenziali del client** — [Client torrent](clients.md)

I valori non configurati restano `no_key` / `no_pass` / `no_path`.

## Verifica la configurazione

```bash
ittup -check
```

Controlla i file di configurazione e l'ambiente. All'avvio il bot mostra sempre i percorsi attivi:

```text
[Configuration] '~/ittup_config/ittup.json'
[*.torrent Archive] '~/ittup_config/torrent_archive_path'
[Images,Tmdb cache] '~/ittup_config/cache_path'
[Watcher] '~/ittup_config/watcher_path'
[Watcher] '~/ittup_config/watcher_destination_path'
[Watcher quarantine] '~/ittup_config/watcher_quarantine_path'
[Preferred Language] 'all'
[Youtube Preferred Language] 'IT'
```

!!! danger "Errori bloccanti"
    Se un valore è malformato il bot esce subito con un messaggio tipo `-> Please Fix 'CAMPO' ['valore'] in settings.json`: apri `ittup.json` e correggi il campo indicato.
