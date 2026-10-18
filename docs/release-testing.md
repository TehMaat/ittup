# Release candidate: manual tests

During the soak period (3-5 days) at least one person uses the rc on real uploads and ticks this list in the
milestone issue. Report problems with the Bug form, channel `rc`, label `found-in:rc`.

## Installation

- [ ] Clean install, in a new virtualenv: `pip install --pre ittup==X.Y.ZrcN`
- [ ] ITTup prints `X.Y.ZrcN` when it starts
- [ ] Upgrade from the last release: `pip install ittup==<last release>`, then `pip install --upgrade --pre ittup==X.Y.ZrcN`
- [ ] Linux (Debian/Ubuntu) and, if possible, Windows

## Configuration

- [ ] An existing configuration of the last release is upgraded without losing values (new options get their default)
- [ ] `ittup -check` on the upgraded configuration
- [ ] Without a configuration: the first start creates it and `ittup --help` works

## Main commands

- [ ] Movie upload: `ittup -u <file>` (metadata, screenshots, torrent, upload)
- [ ] Series/season upload: `ittup -f <folder>`
- [ ] Scan: `ittup -scan <folder>`
- [ ] Duplicate check (`-dup`) and torrent only (`-noup`)
- [ ] Watcher (`-watcher`) on a test folder
- [ ] Reseed (`-reseed`)
- [ ] The torrent client in use (qBittorrent, Transmission or rTorrent) receives the torrent
- [ ] Game and document uploads, if the milestone touched them
- [ ] The features and fixes of the milestone, one by one (from the release PR changelog)

## Rollback

- [ ] `pip install ittup==<last release>` goes back and works with the configuration the rc used
