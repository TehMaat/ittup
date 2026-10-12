# Installazione su seedbox ultra.cc

Ultra.cc non permette l'uso di `sudo`, quindi non possiamo usare i pacchetti di sistema. Il bot inoltre ha bisogno di un Python con **sqlite3**, che usa come cache per screenshot e ricerche sul tracker: il Python compilato da pyenv su ultra.cc ne è privo, perché mancano i file di sviluppo di sqlite3.

La via più semplice è [**uv**](https://docs.astral.sh/uv/): si installa senza `sudo`, scarica un Python già pronto che include sqlite3 e installa il bot in un ambiente tutto suo. Niente da compilare.

## 1. Installare uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Carica il nuovo `PATH` nella sessione corrente (oppure esci e rientra in SSH):

```bash
source $HOME/.local/bin/env
```

## 2. Installare il bot

```bash
uv tool install --python 3.12 git+https://github.com/TehMaat/ittup
```

uv scarica da solo Python 3.12 (il bot richiede Python 3.10 minimo; consigliata la 3.12 — le versioni più recenti risultano ancora troppo nuove per alcune librerie). Il comando `ittup` finisce in `~/.local/bin`.

## 3. Testare il bot

```bash
ittup
```

I messaggi in rosso ti avvertono che non hai ancora configurato il bot: prosegui con la [Configurazione minima](../config/intro.md).

## Aggiornare

```bash
uv tool upgrade ittup
```

## Alternativa: pyenv e sqlite3 compilato a mano

Se preferisci usare il **pyenv** preinstallato su ultra.cc, devi prima compilare sqlite3 nella tua home, altrimenti Python viene compilato senza e il bot si ferma con `this Python was built without sqlite3`.

??? note "Passaggi manuali"

    Scarica, compila e installa sqlite3 in `~/sqlite`:

    ```bash
    cd ~
    wget https://sqlite.org/2026/sqlite-autoconf-3510300.tar.gz
    tar xvf sqlite-autoconf-3510300.tar.gz
    cd sqlite-autoconf-3510300
    ./configure --prefix=$HOME/sqlite
    make
    make install
    ```

    Imposta le variabili d'ambiente **solo per questa sessione**:

    ```bash
    export PATH=$HOME/sqlite/bin:$PATH
    export LDFLAGS="-L$HOME/sqlite/lib"
    export CPPFLAGS="-I$HOME/sqlite/include"
    export PKG_CONFIG_PATH="$HOME/sqlite/lib/pkgconfig"
    export PYTHON_CONFIGURE_OPTS="--enable-loadable-sqlite-extensions"
    export LD_LIBRARY_PATH=$HOME/sqlite/lib:$LD_LIBRARY_PATH
    ```

    Installa Python 3.12, impostalo come default e installa il bot:

    ```bash
    pyenv install -f 3.12.0
    pyenv global 3.12.0
    pip install git+https://github.com/TehMaat/ittup
    ```

    Se pyenv non è presente, installalo con `curl -fsSL https://pyenv.run | bash` (istruzioni sul [GitHub di pyenv](https://github.com/pyenv/pyenv?tab=readme-ov-file#linuxunix)).
