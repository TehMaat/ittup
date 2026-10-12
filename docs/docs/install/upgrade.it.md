# Aggiornamento

Quando esce una nuova versione:

```bash
pip install --upgrade git+https://github.com/TehMaat/ittup
```

La versione installata è visibile all'avvio del bot:

```text
ittup 1.1.0 Checking your configuration file..
```

!!! tip "Dopo ogni aggiornamento"
    Lancia un controllo della configurazione: le nuove versioni possono introdurre nuove chiavi nel file di config.

    ```bash
    ittup -check
    ```

Le novità di ogni release sono nella pagina [Releases del progetto](https://github.com/TehMaat/ittup/releases).

## Arrivi da Unit3Dup

ittup è un fork di [Unit3Dup](https://github.com/31December99/Unit3Dup) ridotto alla sola ItaTorrents. Per passare a ittup:

1. Disinstalla Unit3Dup — così vengono rimossi anche i vecchi moduli `common`, `view` e `unit3dup` che aveva installato:

    ```bash
    pip uninstall unit3dup
    ```

2. Installa ittup:

    ```bash
    pip install git+https://github.com/TehMaat/ittup
    ```

3. Avvialo una volta:

    ```bash
    ittup
    ```

Al primo avvio, se esiste `Unit3Dup_config` e non esiste ancora `ittup_config`, ittup **copia** la tua configurazione nella nuova cartella:

| Unit3Dup | ittup |
|---|---|
| `Unit3Dup_config/Unit3Dbot.json` | `ittup_config/ittup.json` |
| `Unit3Dup_config/tags_list.json` | `ittup_config/tags_list.json` |
| `Unit3Dup_config/sign_list.json` | `ittup_config/sign_list.json` |
| `Unit3Dup_config/ban_list.json` | `ittup_config/ban_list.json` |

La vecchia cartella non viene toccata: da qui in avanti modifica solo i file in `ittup_config`.

Le impostazioni dei tracker rimossi (`SIS_*`, `PTT_*`, `AST_*`) e `MULTI_TRACKER` vengono semplicemente ignorate, e i flag `-tracker` / `-mt` non esistono più: ogni upload va su ItaTorrents.

!!! note "I tuoi percorsi personalizzati restano"
    `TORRENT_ARCHIVE_PATH`, `CACHE_PATH` e i percorsi del watcher vengono copiati così come sono: se puntavano dentro `Unit3Dup_config`, continueranno a farlo. Impostali a `no_path` per usare i nuovi default dentro `ittup_config`.
