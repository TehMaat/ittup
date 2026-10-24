# Installation on an ultra.cc seedbox

Ultra.cc does not allow `sudo`, so we can't use the system packages. The bot also needs a Python with **sqlite3**, which it uses as a cache for screenshots and tracker searches: the Python that pyenv builds on ultra.cc doesn't have it, because the sqlite3 development files are missing.

The simplest way is [**uv**](https://docs.astral.sh/uv/): it installs without `sudo` and downloads a ready-made Python that already includes sqlite3, with which you create the bot's virtualenv. Nothing to compile.

## 1. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Load the new `PATH` in the current session (or log out and back in over SSH):

```bash
source $HOME/.local/bin/env
```

## 2. Install the bot

```bash
uv venv --seed --python 3.12 ~/.venvs/ittup
~/.venvs/ittup/bin/pip install ittup
ln -sf ~/.venvs/ittup/bin/ittup ~/.local/bin/ittup
```

uv downloads Python 3.12 by itself and creates the virtualenv with pip in it (`--seed`): the bot requires Python 3.10 minimum; 3.12 is recommended — newer versions are still too recent for some libraries. The link puts the `ittup` command in `~/.local/bin`, already in the `PATH` after step 1.

## 3. Test the bot

```bash
ittup
```

The red messages warn you that the bot is not configured yet: continue with the [minimal configuration](../config/intro.md).

## Upgrade

```bash
~/.venvs/ittup/bin/pip install --upgrade ittup
```

## Alternative: pyenv and sqlite3 compiled by hand

If you'd rather use the **pyenv** preinstalled on ultra.cc, you first have to compile sqlite3 in your home, otherwise Python is built without it and the bot stops with `this Python was built without sqlite3`.

??? note "Manual steps"

    Download, compile and install sqlite3 in `~/sqlite`:

    ```bash
    cd ~
    wget https://sqlite.org/2026/sqlite-autoconf-3510300.tar.gz
    tar xvf sqlite-autoconf-3510300.tar.gz
    cd sqlite-autoconf-3510300
    ./configure --prefix=$HOME/sqlite
    make
    make install
    ```

    Set the environment variables **for this session only**:

    ```bash
    export PATH=$HOME/sqlite/bin:$PATH
    export LDFLAGS="-L$HOME/sqlite/lib"
    export CPPFLAGS="-I$HOME/sqlite/include"
    export PKG_CONFIG_PATH="$HOME/sqlite/lib/pkgconfig"
    export PYTHON_CONFIGURE_OPTS="--enable-loadable-sqlite-extensions"
    export LD_LIBRARY_PATH=$HOME/sqlite/lib:$LD_LIBRARY_PATH
    ```

    Install Python 3.12, set it as the default and install the bot:

    ```bash
    pyenv install -f 3.12.0
    pyenv global 3.12.0
    pip install ittup
    ```

    If pyenv is missing, install it with `curl -fsSL https://pyenv.run | bash` (instructions on the [pyenv GitHub page](https://github.com/pyenv/pyenv?tab=readme-ov-file#linuxunix)).
