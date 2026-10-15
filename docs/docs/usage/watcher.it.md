# Watcher

Il watcher è la modalità **automatica**: il bot monitora una cartella e carica sul tracker tutto quello che ci arriva dentro. Utile in coppia con un client che scarica in una cartella fissa.

## Avvio

```bash
ittup -watcher
```

Il flag non accetta parametri: tutto si configura in `ittup.json`.

## Configurazione

In `user_preferences` ([Opzioni avanzate](../config/options.md#watcher)):

```json
"WATCHER_INTERVAL": 60,
"WATCHER_TIMEOUT": 3600,
"WATCHER_PATH": "/percorso/cartella/sorgente",
"WATCHER_DESTINATION_PATH": "/percorso/cartella/destinazione",
"WATCHER_QUARANTINE_PATH": "/percorso/cartella/quarantena",
"WATCHER_MAX_RETRIES": 5,
```

- `WATCHER_PATH` → la cartella **monitorata** (es. dove vengono scaricati i file)
- `WATCHER_DESTINATION_PATH` → la cartella dove i file vengono **spostati** e da cui parte l'upload
- `WATCHER_INTERVAL` → ogni quanti **secondi** scatta il controllo
- `WATCHER_TIMEOUT` → dopo quanti **secondi** un singolo file o cartella viene considerato bloccato (`0` = nessun limite)
- `WATCHER_QUARANTINE_PATH` → la cartella dove finiscono gli upload **falliti** (default: `ittup_config/watcher_quarantine_path`)
- `WATCHER_MAX_RETRIES` → quante volte viene **ritentato** un upload fermato da un errore temporaneo

## Cosa fa a ogni ciclo

Allo scadere di `WATCHER_INTERVAL`:

1. Controlla `WATCHER_PATH`; se è vuota, aspetta il ciclo successivo
2. **Sposta** tutti i file in `WATCHER_DESTINATION_PATH`, preservando le sottocartelle (le cartelle svuotate vengono rimosse), e li aggiunge alla **coda** degli upload
3. Processa la coda **uno alla volta**, in ordine alfanumerico, e **carica sul tracker** con seeding, come uno [`-scan`](upload.md): i file appena spostati e i tentativi da ripetere arrivati alla loro ora
4. Ricomincia

Il loop è infinito: si esce con ++ctrl+c++.

!!! note "Conto alla rovescia e log"
    In un terminale interattivo il conto alla rovescia appare su una sola riga, che viene cancellata quando parte il controllo. Quando l'output finisce in un log (file, pipe, `docker logs`, servizio) il conto alla rovescia non c'è: il bot scrive una sola volta `WATCHDOG: checking the Watcher folder every N seconds` quando resta in attesa, e poi solo quello che succede davvero (file spostati, upload).
!!! info "Restart automatico se un file si blocca"
    Ogni file o cartella viene processato a parte. Se uno si ferma con un errore, o è ancora in corso dopo `WATCHER_TIMEOUT` secondi (es. ffmpeg bloccato su un file corrotto, o una domanda a cui nessuno risponde), il bot lo interrompe, scrive `... Skipped, restarting the watcher` e passa al successivo.
    L'hash dei file molto grandi richiede tempo: se carichi remux pesanti da un disco lento, alza `WATCHER_TIMEOUT`.

## Coda persistente e nuovi tentativi

Ogni file spostato entra subito in una **coda salvata su disco** (`ittup_config/watcher_queue.json`). Se il bot si chiude, va in crash o il server si riavvia, al successivo `ittup -watcher` riprende dagli upload rimasti (`WATCHDOG: N uploads left in the queue by the last run`).

Un upload fermato da un **errore temporaneo** — rete assente, timeout, rate limit, tracker offline o in errore (HTTP 5xx), TMDB che non risponde, un file ancora in corso dopo `WATCHER_TIMEOUT` — viene **ritentato** con un'attesa che raddoppia a ogni tentativo: 1, 2, 4, 8, 16 minuti… fino a un massimo di un'ora. Nel log trovi `Retry 1/5 in 60 seconds`. Mentre aspetta, il watcher continua a caricare gli altri file.

## Quarantena

Un upload che **fallisce per un motivo che non si risolve da solo** (file corrotto, upload rifiutato dal tracker, risoluzione o categoria sconosciute, un errore del bot) oppure che fallisce ancora dopo `WATCHER_MAX_RETRIES` tentativi viene **spostato in `WATCHER_QUARANTINE_PATH`**, invece di restare nel watcher. Accanto trovi un file `<nome>.error.txt` con data, numero di tentativi e motivo:

```text
Date: 2026-10-15 14:02:11
Path: /watcher/destinazione/Film.2020.1080p.mkv
Attempts: 1
Reason:
- 'Film 2020 1080p WEB-DL H.264': upload refused by the tracker: UploadBot - The name has already been taken. :
```

Il `.torrent` mai caricato viene tolto dall'archivio: dopo aver sistemato il problema puoi rimettere il file in `WATCHER_PATH` per riprovare, oppure caricarlo a mano con [`-u`](upload.md).

!!! warning "I file vengono spostati, non copiati"
    `WATCHER_PATH` viene **svuotata** a ogni ciclo. Non puntarla a una cartella i cui file devono restare dove sono (es. quella di seeding del client).

!!! tip "Cartella inesistente?"
    Se `WATCHER_PATH` non esiste o non è configurata, il bot si ferma con `Watcher path does not exist or is not configured`.
