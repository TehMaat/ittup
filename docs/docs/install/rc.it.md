# Release candidate

Prima di ogni release viene pubblicata su [PyPI](https://pypi.org/project/ittup/#history) una **release candidate** (rc), per esempio `1.13.0rc3`, da provare: è la versione che diventerà la release, da usare per qualche giorno su upload veri. pip installa una pre-release solo se glielo chiedi con `--pre`, quindi chi non la chiede non la riceve mai.

!!! warning
    Una rc può avere ancora dei bug: installala se vuoi aiutare a testarla, e [segnala](#segnalare-un-problema) quello che non va.

I comandi sono per Linux, con ITTup in un virtualenv come nella guida [Linux](linux.md). Su Windows usa il `pip` della tua installazione: `pip install --upgrade --pre ittup`.

## Installare una rc

In un nuovo virtualenv, così la tua installazione normale resta com'è:

```bash
python3 -m venv ~/.venvs/ittup-rc
~/.venvs/ittup-rc/bin/pip install --pre ittup
~/.venvs/ittup-rc/bin/ittup
```

Oppure aggiorna la tua installazione normale:

```bash
~/.venvs/ittup/bin/pip install --upgrade --pre ittup
```

`--pre` prende la versione più recente, rc o release. Per una rc precisa: `pip install ittup==1.13.0rc3`.

Il bot mostra la versione all'avvio (`ITTup 1.13.0rc3 ...`); la mostra anche `pip show ittup`.

!!! note "La configurazione è la stessa"
    Ogni installazione usa la stessa cartella `ittup_config`. La rc aggiorna `ittup.json` come ogni nuova versione: le nuove opzioni prendono il valore di default e il file precedente resta come `ittup.json.bak-<data>`.

## La rc successiva

Quando esce una nuova rc (per esempio `1.13.0rc4`, dopo una correzione):

```bash
~/.venvs/ittup-rc/bin/pip install --upgrade --pre ittup
```

## Tornare alla release

| Comando | Cosa fa |
|---|---|
| `pip install --upgrade ittup` | Senza `--pre`, pip prende solo le release e non torna mai indietro: resta sulla rc finché non esce la release successiva (`1.13.0rc3` → `1.13.0`), poi aggiorna. Da lì in poi, solo release. |
| `pip install ittup==1.12.1` | Torna subito alla release che indichi, per esempio la precedente. |

Con un virtualenv separato, torna a usare la tua installazione normale e cancella quello della rc: `rm -rf ~/.venvs/ittup-rc`.

Tornare alla release precedente funziona con la configurazione usata dalla rc: le opzioni che non conosce vengono tolte da `ittup.json` e restano nel backup.

## Avviso di aggiornamento

Con una rc installata, il bot annuncia la release successiva (`ITTup 1.13.0 is available (installed: 1.13.0rc3)`), mai un'altra rc: per la rc successiva usa il comando qui sopra. Fino alla `1.13.0rc3` l'avviso non compariva con una rc installata: aggiorna a mano quando esce la release.

## Segnalare un problema

Apri un [Bug](https://github.com/TehMaat/ittup/issues/new?template=bug.yml) con canale `rc` e la versione esatta (`1.13.0rc3`), oppure scrivi su [Discord](https://discord.gg/VMYaVzq2AF).
