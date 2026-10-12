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
```

- `WATCHER_PATH` → la cartella **monitorata** (es. dove vengono scaricati i file)
- `WATCHER_DESTINATION_PATH` → la cartella dove i file vengono **spostati** e da cui parte l'upload
- `WATCHER_INTERVAL` → ogni quanti **secondi** scatta il controllo
- `WATCHER_TIMEOUT` → dopo quanti **secondi** un singolo file o cartella viene considerato bloccato (`0` = nessun limite)

## Cosa fa a ogni ciclo

Allo scadere di `WATCHER_INTERVAL`:

1. Controlla `WATCHER_PATH`; se è vuota, aspetta il ciclo successivo
2. **Sposta** tutti i file in `WATCHER_DESTINATION_PATH`, preservando le sottocartelle (le cartelle svuotate vengono rimosse)
3. Processa i file spostati **uno alla volta** e li **carica sul tracker** con seeding, come uno [`-scan`](upload.md)
4. Ricomincia

Il loop è infinito: si esce con ++ctrl+c++.

!!! note "Conto alla rovescia e log"
    In un terminale interattivo il conto alla rovescia appare su una sola riga, che viene cancellata quando parte il controllo. Quando l'output finisce in un log (file, pipe, `docker logs`, servizio) il conto alla rovescia non c'è: il bot scrive una sola volta `WATCHDOG: checking the Watcher folder every N seconds` quando resta in attesa, e poi solo quello che succede davvero (file spostati, upload).
!!! info "Restart automatico se un file si blocca"
    Ogni file o cartella viene processato a parte. Se uno si ferma con un errore, o è ancora in corso dopo `WATCHER_TIMEOUT` secondi (es. ffmpeg bloccato su un file corrotto, o una domanda a cui nessuno risponde), il bot lo interrompe, scrive `... Skipped, restarting the watcher` e passa al successivo.
    Il file saltato resta in `WATCHER_DESTINATION_PATH` e non viene ritentato: controllalo e caricalo a mano con [`-u`](upload.md).
    L'hash dei file molto grandi richiede tempo: se carichi remux pesanti da un disco lento, alza `WATCHER_TIMEOUT`.

!!! warning "I file vengono spostati, non copiati"
    `WATCHER_PATH` viene **svuotata** a ogni ciclo. Non puntarla a una cartella i cui file devono restare dove sono (es. quella di seeding del client).

!!! tip "Cartella inesistente?"
    Se `WATCHER_PATH` non esiste o non è configurata, il bot si ferma con `Watcher path does not exist or is not configured`.
