# Tags and titles

The torrent title is made of the **media title** plus a set of **tags** derived from the file analysis: resolution, source, audio/video codec, language, HDR…

Available tags: `version`, `resolution`, `uhd`, `platform`, `source`, `remux`, `multi`, `acodec`, `channels`, `flag`, `subtitle`, `vcodec`, `hdr`.

`video_encoder` is still accepted in `TAGS_POSITION_*` so existing configurations keep working, but it no longer adds anything: the encoder is part of `vcodec`. To leave a tag out of the title, remove it from `TAGS_POSITION_MOVIE` / `TAGS_POSITION_SERIE`.

## How the title is built

For every movie and TV show the bot **builds the title from scratch** using the technical analysis of the media (MediaInfo) and the file name, in the order defined by `TAGS_POSITION_MOVIE` / `TAGS_POSITION_SERIE` ([Advanced options](../config/options.md#tag-order-in-the-title)). It happens on every upload: there is no flag to turn on (the old Unit3Dup `-b` flag no longer exists).

When TMDB finds the movie or TV show, the title is the **Italian title from TMDB**, with its punctuation (`Spider-Man: No Way Home`), also when the file name is in English. Without an Italian translation, or when the TMDB search is skipped, the title comes from the name.

The title from the name keeps the special characters written in it: `Spider-Man.No.Way.Home.2021` gives `Spider-Man No Way Home`, `Mission: Impossible - Dead Reckoning (2023)` keeps the colon and the dash.

## Season and episode packs

A season pack is written `S04`, an episode pack `S04E01-06`, also when the name has a space or a dot between season and episodes (`S04 E01-06`, `S04.E01-06`). On the tracker both have episode number `0` (pack). When the pack has every episode of a season that TMDB has concluded (`S04E01-10` of a 10-episode season), the title says just `S04`.

It **does not rename your file**: it only builds the torrent title shown on the tracker page, unless you turn on [`RENAME_FILES`](../config/options.md#rename-the-files-as-the-title).

## Resolution

The resolution (`resolution` tag, `uhd` tag and resolution on the tracker) is read from the width and the height in MediaInfo, not from the file name. A video that is not 16:9 is reduced on one side only, so the resolution is the highest one reached by either side: a 1920×800 scope movie and a 1440×1080 4:3 or anamorphic one are both `1080p`.

| Resolution | `uhd` | Width ≥ | or height ≥ |
|---|---|---|---|
| `2160p` | UHD | 3200 | 1800 |
| `1080p` | FullHD | 1600 | 900 |
| `720p` | HD | 1100 | 600 |
| `576p` | SD | 960 | 540 |

Below `576p` the resolution is the height (`720×480` → `480p`).

An interlaced video (MediaInfo *Scan type* `Interlaced`, `MBAFF` or `PAFF`) is `1080i`, `576i` or `480i`, the interlaced resolutions of the tracker: `2160p` and `720p` stay progressive.

## Video codec

The codec family (264, 265 or other) is read from the file name (`x264`, `x265`, `H264`, `H.265`, `AVC`, `HEVC`…) or, when missing, from MediaInfo. When the two don't agree MediaInfo wins and the bot shows a warning.

The release type, read from the source/remux tags of the file name, decides how the codec is written:

| Release type | Tags | Codec |
|---|---|---|
| Untouched | `REMUX`, `BDREMUX`, `BDMUX`, `VU`, `UNTOUCHED`, `DVDMUX`, `FULL DISC` | `AVC` / `HEVC` |
| WEB-DL | `WEB-DL`, `WEB`, `WEBDL`, `WEB-DLMUX`, `WEBMUX`, `DLMUX`, `HDTV` | `H.264` / `H.265` |
| Encode | `ENCODE`, `WEBRIP`, `BDRIP`, `BRRIP`, `DVDRIP`, `UHDRIP`, `FHDRIP`, `WEB-DLRIP` | `x264` / `x265` |

With `BLURAY` alone, or no release type in the name, the bot looks at the encoder written by MediaInfo: `x264` / `x265` if it finds the x264/x265 signature, `H.264` / `H.265` otherwise. On an untouched release the x264/x265 signature only shows a "possible fake REMUX" warning. Other codecs (AV1, VP9, VC-1, MPEG-2, XviD…) are written as they are.

## Source and tracker type

The source written in the name (`WEB-DL`, `WEBRip`, `REMUX`, `DLMux`…) also decides the torrent **type** on the tracker: it wins over the codec and generic tags written before it (`HEVC`, `FullHD`, `BluRay`), so `Movie.2020.1080p.HEVC.WEB-DL` is a WEB-DL and `Movie.2020.1080p.BluRay.REMUX` a Remux. The bot looks at the folder name first, then at the video file name. With no source in the name, a codec (`x264`, `HEVC`…) means Encode.

The source can be between dots, underscores, dashes or brackets (`Movie_2020_BDRip_1080p`, `Movie.2020.(WEB-DL).1080p`). With no year or season in the name, it is also read before the resolution (`Movie_BDRip_1080p`), but only the sources that can't be a word of the title: `Charlotte's Web 1080p` is not a WEB-DL.

Streaming platform rips are split into platform and source: `NFRip` becomes `NF WEBRip` (for every streaming platform the bot knows, e.g. `AMZNRip` → `AMZN WEBRip`).

### Source from MediaInfo

When the file name has no source, the bot tries to read it from MediaInfo and writes it in the title and in the tracker type:

- the release name many files keep in their metadata title (e.g. `Movie.2020.1080p.WEB-DL.H.264-GRP` → `WEB-DL`). A plain title, with no year, season or resolution, is ignored
- the disc the video was ripped from (`Original source medium`, written by MakeMKV and similar tools): `Blu-ray` with the video track copied as it is becomes `BluRay REMUX`, re-encoded with x264/x265 `BluRay`; a re-encoded DVD becomes `DVDRip`

When MediaInfo doesn't tell the source, the title stays without it. The log shows `Source not in the file name: '...' from MediaInfo`.

## Audio codec

The title keeps at most two audio codecs: the **best ITA codec** and the **best codec in the original language** of the movie or show (read from TMDB, English when TMDB doesn't know it). When there is room left, it is filled with the best tracks with no language. Codecs from the best one: `TrueHD`, `DTS-HD MA`, `FLAC`, `PCM`, `DTS-ES`, `DTS`, `DD+`, `DD`, `AAC`, `HE-AAC`, `Opus`, `MPEG`. With the same codec, Atmos and then more channels win. The same codec is written once. After the codec come the channels read from MediaInfo: `1.0`, `2.0`, `5.1` or `7.1`.

The languages follow the codecs: only `ITA` and the original language are written, the other languages of the file become the `multi` tag (`MULTI`). Example with Italian, English and Japanese tracks of a Japanese movie: `MULTI DD 5.1 DTS-HD MA 5.1 ITA JPN`; with only Italian and Japanese tracks there is no `MULTI`. A file with neither Italian nor the original language gets the flag of its first language.

## Release group

The title ends with the release group, read from the end of the file or folder name after a `-`, a `.`, a space or in `[ ]`:

| Name | Release group |
|---|---|
| `Movie.2024.1080p.WEB-DL.DDP5.1.H.264-NAHOM.mkv` | `-NAHOM` |
| `Movie.2025.1080p.VU.REMUX.TrueHD.ITA.ENG.AVC.LFi.mkv` | `-LFi` |
| `Show.S01E03.1080p.WEB-DL.E-AC3.ITA.KOR.SUBS.H.264.S-K.mkv` | `-S-K` |
| `Movie (2022) iTA-ENG.Bluray.1080p.x264-Dr4gon MIRCrew.mkv` | `-Dr4gon MIRCrew` |
| `Movie.2024.1080p.BluRay.x264.AC3.ITA-ENG.mkv` | none: `ENG` is a language |
| `Spider-Man.2002.1080p.BluRay.x264.mkv` | none: `Spider` is part of the title |

A language (`ITA`, `ENG`…) or `MULTI`, `DUAL`, `SUB`, `SUBS` at the end of the name is never a release group.

To choose it yourself:

- `-tag NAME` for one upload: `ittup -u "<file>" -tag NAHOM`
- `RELEASER_SIGN` in `ittup.json` for every upload ([Advanced options](../config/options.md#language-anonymity-and-signature)), max 20 characters, special characters stripped

`-tag` wins over `RELEASER_SIGN`, and both win over the name.

!!! note "`tags_list.json`, `sign_list.json`, `ban_list.json`"
    Up to 1.x the bot copied these three lists into `ittup_config`. Since 2.0 the tags and the release groups come with ITTup and are updated with it: the files are no longer read, and the bot says so at startup while they are still there. You can delete them. What `ban_list.json` did (leave a tag out of the title) is done by `TAGS_POSITION_*`.

## Manual title

When the file name is too messy to extract a title from (typical with season packs without a title):

```bash
ittup -u "/path/S01.pack.1080p.mkv" -notitle "Show Name"
```

`-notitle` forces the title used for the **TMDB search**, without touching the technical tags.
