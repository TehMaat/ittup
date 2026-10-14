# Changelog

## [1.4.0](https://github.com/TehMaat/ittup/compare/1.3.0...1.4.0) (2026-10-14)


### Features

* add RENAME_FILES to rename the original files as the tracker title ([968cbfe](https://github.com/TehMaat/ittup/commit/968cbfeff442ab8399bca7324b6c2a0e62b64d45)), closes [#38](https://github.com/TehMaat/ittup/issues/38)
* add the -fl25, -fl50, -fl75 and -fl100 freeleech upload flags ([7f90807](https://github.com/TehMaat/ittup/commit/7f908073c85f37556d3dafa067a667098db23131)), closes [#42](https://github.com/TehMaat/ittup/issues/42)
* Italian TMDB titles, freeleech flags, file renaming and title/type fixes ([1915578](https://github.com/TehMaat/ittup/commit/1915578a45af746d468da7452eaa7552cb3df125))
* print the generated display name on a single line ([6ef5001](https://github.com/TehMaat/ittup/commit/6ef50018c591d0dc246b9c34436699d0198ac138)), closes [#37](https://github.com/TehMaat/ittup/issues/37)
* upload the -scan and -watcher contents in alphanumeric order ([66a9392](https://github.com/TehMaat/ittup/commit/66a93929c703a3cb4e9dd2f491f55cce5fe3a56c)), closes [#33](https://github.com/TehMaat/ittup/issues/33)
* write NFRip and the other platform rips as the platform plus WEBRip ([325e92f](https://github.com/TehMaat/ittup/commit/325e92f7fa141063c8e90c21157dd00bef03ef06)), closes [#34](https://github.com/TehMaat/ittup/issues/34)
* write the Italian title from TMDB in the torrent name ([e300216](https://github.com/TehMaat/ittup/commit/e30021690e15a9f59ca0c3a0b3bdd2609f0b1b8b)), closes [#31](https://github.com/TehMaat/ittup/issues/31)


### Bug Fixes

* find the TMDB ID of the titles with brackets and of more ID formats ([c52b1ce](https://github.com/TehMaat/ittup/commit/c52b1ce78f5ce6ba27f8ecea3fe94109a1fa6e58)), closes [#35](https://github.com/TehMaat/ittup/issues/35)
* keep the special characters of the title written in the name ([6e9eaee](https://github.com/TehMaat/ittup/commit/6e9eaee4cb24cc04fb4961d39cf4e51e802eceaa)), closes [#40](https://github.com/TehMaat/ittup/issues/40)
* pick the tracker type from the source written in the release name ([f8e77ba](https://github.com/TehMaat/ittup/commit/f8e77ba624c104e903c8afdd6c115a172c86e5a6)), closes [#36](https://github.com/TehMaat/ittup/issues/36)
* read the episode packs written as Sxx Exx-xx ([593be56](https://github.com/TehMaat/ittup/commit/593be56f9183523e8ff3cf12cbc6ce9d350107eb)), closes [#32](https://github.com/TehMaat/ittup/issues/32)
* read the lower case season packs and not DTS5.1 as a season ([0cb3b01](https://github.com/TehMaat/ittup/commit/0cb3b01f0ead36ad2dbbc2ba0596167ab50eb96a)), closes [#32](https://github.com/TehMaat/ittup/issues/32)
* rename the files with characters refused by the tracker before the upload ([e6a963b](https://github.com/TehMaat/ittup/commit/e6a963b0166b9531f0110f6a1f04ef4d62f10374)), closes [#41](https://github.com/TehMaat/ittup/issues/41)


### Documentation

* install with pipx on Linux ([a3fdeab](https://github.com/TehMaat/ittup/commit/a3fdeab10e707231413d3fb95970cefa3fe36f4f))
* install with pipx on Linux ([a415c36](https://github.com/TehMaat/ittup/commit/a415c364031ae088b70df76eda15c2ce770e9632))

## [1.3.0](https://github.com/TehMaat/ittup/compare/1.2.3...1.3.0) (2026-10-12)


### Features

* keep only the two best ITA/ENG audio codecs in the title ([6d77b9b](https://github.com/TehMaat/ittup/commit/6d77b9b659d3d5f49f368a5a28d72b74fa021f18))
* write only the ITA and original language audio codecs in the title ([cd9e0bd](https://github.com/TehMaat/ittup/commit/cd9e0bdf20cd59d0e274d42347ed9ea1924b9e80))
* write the best ITA and the best ENG audio codec in the title ([b8b5f06](https://github.com/TehMaat/ittup/commit/b8b5f06cdab43f31b5c8956c6ce78ac67a264fc2))
* write the ITA and original language audio codecs, other languages only as flags ([ac2a71f](https://github.com/TehMaat/ittup/commit/ac2a71f81db8c958e70870bddf3cc53c0bd7188a))

## [1.2.3](https://github.com/TehMaat/ittup/compare/1.2.2...1.2.3) (2026-10-12)


### Bug Fixes

* check for duplicates before creating the torrent file ([cc42a5c](https://github.com/TehMaat/ittup/commit/cc42a5cb27f18cd0cac3c0b99d0b141df1fb113c))
* check for duplicates before creating the torrent file ([81421aa](https://github.com/TehMaat/ittup/commit/81421aa976d284a1a530877bfe498792cf14d5bb))
* stop the watcher from uploading each file twice and crashing on Python 3.14 ([7a3951c](https://github.com/TehMaat/ittup/commit/7a3951cf06117b978af266b68fe14ce7b6af0482))
* stop the watcher from uploading each file twice and crashing on Python 3.14 ([5624470](https://github.com/TehMaat/ittup/commit/5624470f19de375010de0bc4db9889ae2f44e0aa))

## [1.2.2](https://github.com/TehMaat/ittup/compare/1.2.1...1.2.2) (2026-10-12)


### Bug Fixes

* remove leftover separator line from MY_TEXT_H in the default config ([315822c](https://github.com/TehMaat/ittup/commit/315822c76371904fb6d4fd88c24707d42ec31fa8))
* remove leftover separator line from MY_TEXT_H in the default config ([66f67ac](https://github.com/TehMaat/ittup/commit/66f67ac7664eea9b9e8b44305a4d7b0fa75de7ca))
* write the video codec from the release type in the title ([25d455d](https://github.com/TehMaat/ittup/commit/25d455df41601132675fceebbab3503cb73da288))
* write the video codec from the release type in the title ([a1b9fc1](https://github.com/TehMaat/ittup/commit/a1b9fc13af405c2c3caaf2c8af7ca967dbff274e))

## [1.2.1](https://github.com/TehMaat/ittup/compare/1.2.0...1.2.1) (2026-10-12)


### Bug Fixes

* repair broken merge of the immediate-seeding change ([bb1ef2d](https://github.com/TehMaat/ittup/commit/bb1ef2dd02339703b4adeaa55be61e85e0e43970))

## [1.2.0](https://github.com/TehMaat/ittup/compare/1.1.0...1.2.0) (2026-10-12)


### Features

* send each torrent to the client right after its upload ([c93ad5c](https://github.com/TehMaat/ittup/commit/c93ad5c54da7257c34e464d0d61c6e9441463ed6))
* send each torrent to the client right after its upload ([57003eb](https://github.com/TehMaat/ittup/commit/57003eb49cb5d2f389d30aacefdd15508d5f771e))
* send each torrent to the client right after its upload in scan and watcher ([3f14056](https://github.com/TehMaat/ittup/commit/3f14056f6c77ce255db3a9c635313aa3b54e3421))
* send each torrent to the client right after its upload in scan and watcher ([375ac1f](https://github.com/TehMaat/ittup/commit/375ac1f83e6fac980a3e044bf4ca575d4bd875f5))
* skip files that hang or crash in the watcher and keep going ([a89c183](https://github.com/TehMaat/ittup/commit/a89c183247bb1ceb6211e29e774c7a97b6b5d778))
* skip files that hang or crash in the watcher and keep going ([129e16a](https://github.com/TehMaat/ittup/commit/129e16ad99abe53f1a708c3762723e8d30e1f702))


### Bug Fixes

* install on ultra.cc with uv instead of compiling sqlite3 by hand ([48aaf1d](https://github.com/TehMaat/ittup/commit/48aaf1d8657db4f583a01efd998fe5b568cc5ae9))
* install on ultra.cc with uv instead of compiling sqlite3 by hand ([36b2221](https://github.com/TehMaat/ittup/commit/36b222141baffd7678ef5bac8f1231d61446feb8))
* stop the watcher countdown from writing one log line per second ([16c51d6](https://github.com/TehMaat/ittup/commit/16c51d671dc4f7e102f564c6ac00d110ab06e8f6))
* stop the watcher countdown from writing one log line per second ([b05f2d2](https://github.com/TehMaat/ittup/commit/b05f2d2f16ec6079c76ade5a7fc8288fe83cc59e))
* use the IMDb ID when looking up and uploading media ([2e6d244](https://github.com/TehMaat/ittup/commit/2e6d2445331a244cd7b441013c33b4d552fdffc6))
* use the IMDb ID when looking up and uploading media ([cddaf91](https://github.com/TehMaat/ittup/commit/cddaf91c4f2ceb10d464dfe87214af9789529645))
