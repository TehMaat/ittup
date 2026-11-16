# Aggiornamento

Quando esce una nuova versione:

!!! tip
    A ogni avvio il bot chiede a PyPI l'ultima versione e, se ce n'è una più recente, mostra `ITTup X.Y.Z is available (installed: ...)` dopo il riepilogo della configurazione, con il link alle note di rilascio e gli altri processi ITTup attivi. È solo un messaggio: il bot continua con la versione installata, e se PyPI non risponde entro un secondo non viene mostrato nulla. Vengono annunciate solo le release, mai le [release candidate](rc.md).

## Con `ittup --upgrade`

```bash
ittup --upgrade
```

Installa la nuova versione con il `pip` del Python che esegue ITTup (lo stesso virtualenv). Se un watcher, uno scan, un reseed o un upload è ancora in esecuzione, aggiornare lo fermerebbe a metà o lo lascerebbe girare con il codice vecchio: vengono elencati e il bot chiede cosa fare.

```text
⚠ ITTup processes running: 1
  PID 12345   watcher   started 2026-10-16 10:02   working on: Film.2024.1080p.mkv
Upgrading now can stop an upload halfway.
[W]ait for them to end / [S]top them and upgrade (a watcher ends its upload first) / [F]orce the upgrade / [N]o, cancel:
```

| Risposta | Argomento | Cosa succede |
|---|---|---|
| Wait | `ittup --upgrade wait` | Aspetta che finiscano, poi aggiorna |
| Stop | `ittup --upgrade stop` | Manda loro un SIGTERM: il watcher finisce l'upload in corso ed esce, gli altri comandi si fermano subito. Poi aggiorna. Non su Windows |
| Force | `ittup --upgrade force` | Aggiorna subito: riavviali dopo |
| No | — | Annulla |

Gli argomenti rispondono alla domanda in uno script o in un cron; senza terminale e senza argomento l'aggiornamento viene annullato. `ittup --upgrade check` controlla e basta: exit code 0 se ITTup è aggiornato, 1 se è uscita una nuova versione, 2 se PyPI non risponde.

Un watcher che si accorge di una nuova versione installata sotto di lui (per esempio con `pip` a mano) si ferma prima dell'upload successivo: riavvialo.

## Con pip

Aggiorna con il `pip` dell'ambiente in cui hai installato ITTup. In un virtualenv (come nelle guide [Linux](linux.md) e [Seedbox ultra.cc](seedbox.md)):

```bash
~/.venvs/ittup/bin/pip install --upgrade ittup
```

Senza virtualenv (come nella guida [Windows](windows.md)), o con il virtualenv attivo:

```bash
pip install --upgrade ittup
```

Senza `--pre`, pip installa solo le release e non torna mai a una versione più vecchia.

!!! note "Installato con pipx o uv tool?"
    Le versioni precedenti di queste guide installavano il bot con pipx (Linux) o `uv tool` (seedbox). Passa a un virtualenv una volta sola: `pipx uninstall ittup` o `uv tool uninstall ittup`, poi installalo di nuovo seguendo la guida. La configurazione in `ittup_config` resta.

!!! note "Installato da GitHub?"
    Fino alla 1.5.0 il bot si installava da GitHub (`git+https://github.com/TehMaat/ittup`). Ora è su [PyPI](https://pypi.org/project/ittup/): passa a PyPI una volta sola con `pip install --upgrade ittup`, poi aggiorna con i comandi qui sopra.

La versione installata è visibile all'avvio del bot:

```text
ITTup 1.1.0 Checking your configuration file..
```

!!! tip "Dopo ogni aggiornamento"
    Lancia un controllo della configurazione: le nuove versioni possono introdurre nuove chiavi nel file di config.

    ```bash
    ittup -check
    ```

Le novità di ogni release sono nella pagina [Releases del progetto](https://github.com/TehMaat/ittup/releases).

## Arrivi da Unit3Dup

ITTup è un fork di [Unit3Dup](https://github.com/31December99/Unit3Dup) ridotto alla sola ItaTorrents. Per passare a ITTup:

1. Installa ITTup:

    ```bash
    pip install ittup
    ```

2. Avvialo una volta:

    ```bash
    ittup
    ```

Al primo avvio, se esiste `Unit3Dup_config` e non esiste ancora `ittup_config`, ITTup **copia** la tua configurazione nella nuova cartella:

| Unit3Dup | ITTup |
|---|---|
| `Unit3Dup_config/Unit3Dbot.json` | `ittup_config/ittup.json` |

La vecchia cartella non viene toccata: da qui in avanti modifica solo i file in `ittup_config`.

Le impostazioni dei tracker rimossi (`SIS_*`, `PTT_*`, `AST_*`) e `MULTI_TRACKER` vengono semplicemente ignorate, e i flag `-tracker` / `-mt` non esistono più: ogni upload va su ItaTorrents.

!!! note "I tuoi percorsi personalizzati restano"
    `TORRENT_ARCHIVE_PATH`, `CACHE_PATH` e i percorsi del watcher vengono copiati così come sono: se puntavano dentro `Unit3Dup_config`, continueranno a farlo. Impostali a `no_path` per usare i nuovi default dentro `ittup_config`.

## Tenere anche Unit3Dup

Non devi per forza disinstallare Unit3Dup: i due possono restare installati insieme. Hanno comandi diversi (`unit3dup` e `ittup`), tutto il codice di ITTup sta nel solo pacchetto `ittup` e ognuno ha la sua cartella di configurazione.

Se li usi tutti e due, tieni presente che:

- I percorsi personalizzati copiati dalla configurazione di Unit3Dup (vedi la nota sopra) sono in comune tra i due. Non far girare i due watcher sulla stessa cartella, altrimenti gli stessi file possono essere caricati due volte: dai a ITTup cartelle sue in `ittup.json`, oppure impostale a `no_path`.
- Se il tuo Unit3Dup è più vecchio della 0.14.x, installare ITTup nello stesso ambiente può aggiornare librerie che usa anche Unit3Dup. Per tenerli separati, installa ITTup in un suo virtualenv, come nella guida [Linux](linux.md).

Quando Unit3Dup non ti serve più, disinstallalo — così vengono rimossi anche i vecchi moduli `common`, `view` e `unit3dup` che aveva installato:

```bash
pip uninstall unit3dup
```
