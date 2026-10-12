# Tracker

Sezione `tracker_config` di `ittup.json`.

ittup carica solo su **ItaTorrents** (ITT): non c'è un tracker da scegliere né una lista multi-tracker.

## Le tre chiavi di ITT

| Chiave | Cos'è | Dove si trova |
|---|---|---|
| `ITT_URL` | Indirizzo del tracker | Già precompilato nel file di default |
| `ITT_APIKEY` | La tua API key personale | Sul tracker: profilo utente → impostazioni → API |
| `ITT_PID` | La tua passkey (PID) | Sul tracker: pagina sicurezza del profilo |

```json
"ITT_URL": "https://itatorrents.xyz",
"ITT_APIKEY": "la_tua_api_key",
"ITT_PID": "la_tua_passkey",
```

- **`ITT_APIKEY`** serve per ogni comunicazione col tracker: upload, ricerche, controllo duplicati
- **`ITT_PID`** serve per generare l'announce URL del torrent: senza, il torrent che metti in seeding non può annunciarsi al tracker

All'avvio il bot verifica che il tracker risponda:

```text
Tracker -> 'ITT' Online
```

!!! note "Residui di Unit3Dup"
    Se il tuo `ittup.json` è stato copiato da Unit3Dup, può contenere ancora `SIS_*`, `PTT_*`, `AST_*` e `MULTI_TRACKER`: vengono ignorati, puoi cancellarli.
