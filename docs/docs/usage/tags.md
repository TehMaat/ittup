# Tags and titles

The torrent title is made of the **media title** plus a set of **tags** derived from the file analysis: resolution, source, audio/video codec, language, HDR…

Available tags: `version`, `resolution`, `uhd`, `platform`, `source`, `remux`, `multi`, `acodec`, `channels`, `flag`, `subtitle`, `vcodec`, `hdr`.

`video_encoder` is still accepted in `TAGS_POSITION_*` and in `ban_list.json` so existing configurations keep working, but it no longer adds anything: the encoder is part of `vcodec`.

## How the title is built

For every movie and TV show the bot **builds the title from scratch** using the technical analysis of the media (MediaInfo) and the file name, in the order defined by `TAGS_POSITION_MOVIE` / `TAGS_POSITION_SERIE` ([Advanced options](../config/options.md#tag-order-in-the-title)). It happens on every upload: there is no flag to turn on (the old Unit3Dup `-b` flag no longer exists).

The title keeps the special characters written in the name: `Spider-Man.No.Way.Home.2021` gives `Spider-Man No Way Home`, `Mission: Impossible - Dead Reckoning (2023)` keeps the colon and the dash.

## Season and episode packs

A season pack is written `S04`, an episode pack `S04E01-06`, also when the name has a space or a dot between season and episodes (`S04 E01-06`, `S04.E01-06`). On the tracker both have episode number `0` (pack). When the pack has every episode of a season that TMDB has concluded (`S04E01-10` of a 10-episode season), the title says just `S04`.

It **does not rename your file**: it only builds the torrent title shown on the tracker page.

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

Streaming platform rips are split into platform and source: `NFRip` becomes `NF WEBRip` (for every platform in `tags_list.json`, e.g. `AMZNRip` → `AMZN WEBRip`).

## Audio codec

The title keeps at most two audio codecs: the **best ITA codec** and the **best codec in the original language** of the movie or show (read from TMDB, English when TMDB doesn't know it). When there is room left, it is filled with the best tracks with no language. Codecs from the best one: `TrueHD`, `DTS-HD MA`, `FLAC`, `PCM`, `DTS-ES`, `DTS`, `DD+`, `DD`, `AAC`, `HE-AAC`, `Opus`, `MPEG`. With the same codec, Atmos and then more channels win. The same codec is written once.

The languages follow the codecs: `ITA`, the original language, then the other languages of the file, which only get their flag and no codec. Example with Italian, English and Japanese tracks of a Japanese movie: `DD 5.1 DTS-HD MA 5.1 ITA JPN ENG`.

## The three customization files

They live in the configuration folder (`ittup_config`) and are created on first run with default values. They are plain JSON, editable with any text editor.

### `tags_list.json` — custom tags

Maps **word → tag type**: it teaches the bot to recognize words in file names and classify them.

```json
{
    "REMUX": "remux",
    "WEB-DL": "source",
    "AMZN": "platform"
}
```

Used when building the title: when the word appears in the file name, the value lands in the right tag of the title. You can add your own entries (e.g. release group names or unusual sources).

!!! warning "Required file"
    If `tags_list.json` is missing, the bot reports it at startup.

### `ban_list.json` — tags to exclude from the autobuild

Excludes entire **tag types** from the title rebuild: a tag listed here never ends up in the title built by the bot. Keys are the tag names (the same ones used in `TAGS_POSITION_*`); the value is just a placeholder.

Example — never include the video codec in the title:

```json
{
    "vcodec": "banned"
}
```

### `sign_list.json` — releaser signatures

List of signatures recognized as **release groups**. Together with `RELEASER_SIGN` ([Advanced options](../config/options.md#language-anonymity-and-signature)) it manages the signature at the end of the title (max 20 characters, special characters stripped).

## Manual title

When the file name is too messy to extract a title from (typical with season packs without a title):

```bash
ittup -u "/path/S01.pack.1080p.mkv" -notitle "Show Name"
```

`-notitle` forces the title used for the **TMDB search**, without touching the technical tags.
