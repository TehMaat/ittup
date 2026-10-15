# Aggiornamento

Quando esce una nuova versione:

```bash
pip install ittup --upgrade
```

Se l'hai installato con pipx (come nella guida [Linux](linux.md)):

```bash
pipx upgrade ittup
```

Se l'hai installato con uv (come nella guida [Seedbox ultra.cc](seedbox.md)):

```bash
uv tool upgrade ittup
```

!!! note "Installato da GitHub?"
    Fino alla 1.5.0 il bot si installava da GitHub (`git+https://github.com/TehMaat/ittup`). Ora è su [PyPI](https://pypi.org/project/ittup/): passa a PyPI una volta sola con `pip install ittup --upgrade`, `pipx install --force ittup` o `uv tool install --force --python 3.12 ittup`, poi aggiorna con i comandi qui sopra.

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
| `Unit3Dup_config/tags_list.json` | `ittup_config/tags_list.json` |
| `Unit3Dup_config/sign_list.json` | `ittup_config/sign_list.json` |
| `Unit3Dup_config/ban_list.json` | `ittup_config/ban_list.json` |

La vecchia cartella non viene toccata: da qui in avanti modifica solo i file in `ittup_config`.

Le impostazioni dei tracker rimossi (`SIS_*`, `PTT_*`, `AST_*`) e `MULTI_TRACKER` vengono semplicemente ignorate, e i flag `-tracker` / `-mt` non esistono più: ogni upload va su ItaTorrents.

!!! note "I tuoi percorsi personalizzati restano"
    `TORRENT_ARCHIVE_PATH`, `CACHE_PATH` e i percorsi del watcher vengono copiati così come sono: se puntavano dentro `Unit3Dup_config`, continueranno a farlo. Impostali a `no_path` per usare i nuovi default dentro `ittup_config`.

## Tenere anche Unit3Dup

Non devi per forza disinstallare Unit3Dup: i due possono restare installati insieme. Hanno comandi diversi (`unit3dup` e `ittup`), tutto il codice di ITTup sta nel solo pacchetto `ittup` e ognuno ha la sua cartella di configurazione.

Se li usi tutti e due, tieni presente che:

- I percorsi personalizzati copiati dalla configurazione di Unit3Dup (vedi la nota sopra) sono in comune tra i due. Non far girare i due watcher sulla stessa cartella, altrimenti gli stessi file possono essere caricati due volte: dai a ITTup cartelle sue in `ittup.json`, oppure impostale a `no_path`.
- Se il tuo Unit3Dup è più vecchio della 0.14.x, installare ITTup nello stesso ambiente può aggiornare librerie che usa anche Unit3Dup. Per tenerli separati, installa ITTup con pipx o in un virtualenv:

    ```bash
    pipx install ittup
    ```

Quando Unit3Dup non ti serve più, disinstallalo — così vengono rimossi anche i vecchi moduli `common`, `view` e `unit3dup` che aveva installato:

```bash
pip uninstall unit3dup
```
