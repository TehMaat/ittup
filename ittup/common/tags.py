# -*- coding: utf-8 -*-
import re
from ittup.common.utility import ManageTitles
from ittup.common.mediainfo import MediaFile
from ittup.core.media import Media
from ittup.view import custom_console

# From hdr format
hdr_map = {
    "DOLBY VISION": "DV",
    "DOLBY VISION DV": "DV",
    "DOLBY VISION HDR": "DV HDR",
    "DOLBY VISION HDR10": "DV HDR10",
    "DOLBY VISION HDR10+": "DV HDR10+",
    "HDR10PLUS": "HDR10+",
    "HDRPLUS+": "HDR10+",
    "HDR10+": "HDR10+",
    "HDR10": "HDR10",
    "BLU-RAY / HDR10": "HDR10",
    "BLU-RAY / HDR10+": "HDR10+",
    "HDR10 / HDR10": "HDR10",
    "HDR10 / HDR10 / HDR10": "HDR10",
    "HDR10 / HDR10+": "HDR10+",
    "HDR10 / HDR10 / HDR10+": "HDR10+",
    "SMPTE ST 2086": "HDR10",
    "SMPTE ST 2094": "HDR10+",

    "DOVI": "DV",
    "HDR": "HDR",
}

audio_translate = {
    "AC3": "DD",
    "AAC LC": "AAC",
    "AAC LC SBR": "HE-AAC",
    "AC-3": "DD",
    "EAC3": "DD+",
    "E-AC3": "DD+",
    "E-AC-3": "DD+",
    "E-AC-3 JOC": "DD+",
    "DTS": "DTS",
    "DTS ES": "DTS-ES",
    "DTS ES XLL": "DTS-HD MA",
    "DTS XLL": "DTS-HD MA",
    "MLP FBA 16-ch": "TrueHD",
    "MPEG Audio": "MPEG",
}

# Channels written in the title from the number of channels of the track
audio_channels = {1: "1.0", 2: "2.0", 6: "5.1", 8: "7.1"}

# Audio codecs from the best to the worst: only the best ones go in the title
audio_rank = ["TrueHD", "DTS-HD MA", "FLAC", "PCM", "DTS-ES", "DTS", "DD+", "DD", "AAC", "HE-AAC", "Opus", "MPEG"]
# The title keeps the best ITA codec and the best codec in the original language, then fills up to
# MAX_AUDIO_CODECS with the tracks with no language. Tracks in other languages only add their flag
MAX_AUDIO_CODECS = 2
# Original language (TMDB ISO 639-1) when it is not known yet
DEFAULT_ORIGINAL_LANGUAGE = "en"

# Codec family from the MediaInfo 'format' of the video track
video_family = {
    "AVC": "264",
    "HEVC": "265",
}

# Release type from the source/remux tags of the file name. Each tag is mapped on its own:
# DLMUX is in the "remux" category but it is a WEB-DL
UNTOUCHED_TAGS = {"REMUX", "BDREMUX", "BDMUX", "VU", "UNTOUCHED", "DVDMUX", "FULL DISC"}
WEB_TAGS = {"WEB-DL", "WEB", "WEBDL", "WEB-DLMUX", "WEBDLMUX", "WEB-MUX", "WEBMUX", "DLMUX", "HDTV"}
ENCODE_TAGS = {"ENCODE", "WEBRIP", "BDRIP", "BRRIP", "DVDRIP", "UHDRIP", "FHDRIP", "WEB-DLRIP", "WEBDLRIP"}

# How each release type writes the 264/265 codec
video_codec_labels = {
    "untouched": {"264": "AVC", "265": "HEVC"},
    "web": {"264": "H.264", "265": "H.265"},
    "encode": {"264": "x264", "265": "x265"},
}

# x264, x.264, H264, H.265, AVC, HEVC... in the file name
NAME_CODEC_PATTERN = re.compile(r'(?<![a-z0-9])(?:[xh][._ -]?26([45])|(avc)|(hevc))(?![a-z0-9])', re.IGNORECASE)

TAG_NORMALIZE = {
    "BLURAY": "BluRay",
    "BLU-RAY": "BluRay",
    "WEB": "WEB-DL",
    "WEBDL": "WEB-DL",
    "WEBMUX": "WEBMux",
    "BDRIP": "BDRip",
    "WEBRIP": "WEBRip",
    "UHDRIP": "UHDRip",
}


class SearchTags(object):
    def __init__(self, filename, title: str, year: str, season: int, episode: int,
                 media: Media, tags_position: list, tags_list: dict, sign_list: dict, ban_list: dict,
                 releaser_sign: str):

        self.mediafile: MediaFile = media.mediafile
        self.tags_position = tags_position
        self.releaser_sign = releaser_sign
        self.media: Media = media
        self.filename = filename
        self.episode = episode
        self.season = season
        self.title = title
        self.year = year
        self.tags_dict = {}
        self.release_type: str | None = None
        self.name_family: str | None = None
        self.original_language: str = DEFAULT_ORIGINAL_LANGUAGE

        self.TAG_TYPES: dict = tags_list
        self.SIGNS_LIST: dict = sign_list
        self.BAN_LIST: dict = ban_list

    @staticmethod
    def normalize_version_tag(tag: str) -> str:
        tag_esc = re.escape(tag)
        return tag_esc

    @staticmethod
    def normalize_part_tag(title: str) -> str | None:
        """
        Extract substring PartX
        Try to remove noisy chars and return a normalized tag
        Part1, Part 1, Part.1, [Part 1], Parte1, Pt1, Prt 2,
        """
        pattern = r'[\[\(]?(?<![^\W_])(?:Part|Parte|Pt|Prt)[\s\._-]*?(\d+)(?![^\W_])[\]\)]?'
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            part_number = match.group(1)
            return f"Part {part_number}"
        return None

    @staticmethod
    def normalize_platform_tag(tag: str) -> str:
        tag_esc = re.escape(tag)
        return tag_esc

    @staticmethod
    def normalize_sources(tag: str) -> str:
        tag_esc = re.escape(tag)
        return tag_esc

    @staticmethod
    def normalize_remux(tag: str) -> str:
        tag_esc = re.escape(tag)
        return tag_esc

    @staticmethod
    def normalize_video_encoder(tag: str) -> str:
        tag_esc = re.escape(tag)
        tag_esc = re.sub(r'([A-Z])(\d+)', r'\1[._-]?\2', tag_esc)
        return tag_esc

    def expand_platform_rip(self, filename: str) -> str:
        """
        Split a platform rip into the platform and the WEBRip source (es. 'NFRip' -> 'NF WEBRip')
        """
        platforms = [tag for tag, category in self.TAG_TYPES.items() if category == "platform"]
        if not platforms:
            return filename
        pattern = r'(?<![a-z0-9])(' + "|".join(re.escape(tag) for tag in platforms) + r')rip(?![a-z0-9])'
        return re.sub(pattern, r'\1 WEBRip', filename, flags=re.IGNORECASE)

    def build_title(self, dictionary: dict) -> str:
        # /// Build the title
        build = []
        for k, v in dictionary.items():
            if isinstance(v, list):
                for item in v:
                    build.append(str(item))
            else:
                build.append(str(v))

        refactored = ' '.join(build) + self.releaser_sign
        return refactored

    def process(self) -> tuple[str, dict]:
        patterns = []

        # Remove banned items from categories
        self.tags_position = [x.lower() for x in self.tags_position if x not in self.BAN_LIST]
        # loop sorted TAG_TYPES dictionary
        for i, (tag, category) in enumerate(
                sorted(self.TAG_TYPES.items(), key=lambda x: len(x[0]), reverse=True)
        ):
            if category == "version":
                norm = self.normalize_version_tag(tag)
            elif category == "platform":
                norm = self.normalize_platform_tag(tag)
            elif category == "remux":
                norm = self.normalize_remux(tag)
            elif category == "source":
                norm = self.normalize_sources(tag)
            elif category == "video_encoder":
                norm = self.normalize_video_encoder(tag)
            else:
                norm = re.escape(tag)
                # Save a regex pattern for each category
            patterns.append([norm, category])

        # NFRip -> NF WEBRip: the streaming platform and the source
        filename = self.expand_platform_rip(self.filename)

        # Run regex: a tag is delimited by anything but a letter or a digit ('Titolo_1990_BDRip_1080p')
        for p, category in patterns:
            regex = re.compile(r'(?<![^\W_])' + p + r'(?![^\W_])', re.IGNORECASE)
            matches = regex.findall(filename)
            if matches:
                # Normalize Tag_list
                normalized_tag = TAG_NORMALIZE.get(matches[0].upper(), None)
                if normalized_tag:
                    matches[0] = normalized_tag
                self.tags_dict.setdefault(category, []).append(matches[0])

        # /// Tags with no categories
        # Identify PartX
        norm = self.normalize_part_tag(self.filename)

        # Remove duplicate regex (findall)
        # es WEB-DL
        if self.tags_dict.get("source", None):
            self.tags_dict["source"] = list(dict.fromkeys(self.tags_dict["source"]))

        # x264/x265 from the file name only tell the codec family: the codec is written by vcodec
        name_encoders = self.tags_dict.pop('video_encoder', [])
        self.name_family = self.codec_family_from_name(self.filename, name_encoders)
        # Read the release type before 'remux' gets the REMUX tag appended below
        self.release_type = self.detect_release_type(
            self.tags_dict.get('source', []) + self.tags_dict.get('remux', [])
        )

        if norm:
            # Skip if it is part of title es: "Wicked.Parte.2.2025.iTA" Title = Wicked Parte 2
            if not any(t in self.title.lower() for t in ['part', 'parte']):
                self.tags_dict.update({'part': norm})

        # /// Read from mediainfo
        updated_category = {}
        for category in self.tags_position:
            if category == "remux":
                remux_tags = self.tags_dict.get('remux', None)
                if remux_tags:
                    if not any('remux' in tag.lower() for tag in remux_tags):
                        remux_tags.append('REMUX')
                        self.tags_dict.update({'remux': remux_tags})

            elif category == "acodec":
                updated_category = self.mediainfo_audio(category=category)

            elif category == "vcodec":
                updated_category = self.mediainfo_video(category=category)

            elif category == "hdr":
                updated_category = self.mediainfo_hdr(category=category)
                if not updated_category:
                    updated_category = {category: 'SDR'}

            elif category == "uhd":
                updated_category = self.mediainfo_uhd(category=category)


            elif category == "subtitle":
                if self.mediafile.subtitle_track:
                    updated_category = {'subtitle': "SUBS" if len(self.mediafile.subtitle_track) > 1 else "SUB"}

            if updated_category:
                self.tags_dict.update(updated_category)

        # /// Add S#E#, title, Year
        if not self.media.torrent_pack:
            se_str = ''
            if self.season is not None and self.episode is not None:
                se_str = f"S{self.season:02d}E{self.episode:02d}"
            elif self.season is not None:
                se_str = f"S{self.season:02d}"
            elif self.episode is not None:
                se_str = f"E{self.episode:02d}"
        else:
            se_str = self.media.pack

        self.tags_dict.update({'title': self.title})
        if self.year:
            self.tags_dict.update({'year': self.year})
        if se_str:
            self.tags_dict.update({'season': se_str})

        if not self.releaser_sign:
            # If releaser_sign is not defined in the configuration file,
            # try to detect a known sign from SIGN_LIST
            self.releaser_sign = self.detect_releaser(self.filename, self.SIGNS_LIST)

        return self.ordered_title()

    def set_original_language(self, original_language: str | None) -> tuple[str, dict]:
        """
        Rebuild the audio tags of the title processed before with the original language from TMDB (es. 'ja')
        """
        self.original_language = (original_language or DEFAULT_ORIGINAL_LANGUAGE).lower()
        if "acodec" in self.tags_position:
            self.tags_dict.update(self.mediainfo_audio(category="acodec"))
        return self.ordered_title()

    def set_title(self, title: str) -> tuple[str, dict]:
        """
        Rebuild the title with a new media title (es. the Italian title from TMDB)
        """
        self.title = title
        self.tags_dict.update({'title': title})
        # The part is already in the new title (es. 'Wicked - Parte 2')
        if re.search(r'(?<![a-z])part[ei]?(?![a-z])', title, re.IGNORECASE):
            self.tags_dict.pop('part', None)
        return self.ordered_title()

    def set_season(self, se_str: str) -> tuple[str, dict]:
        """
        Rebuild the title with a new season tag (es. 'S04' for a pack with every episode of the season)
        """
        self.tags_dict.update({'season': se_str})
        return self.ordered_title()

    def ordered_title(self) -> tuple[str, dict]:
        # /// Order according to tag position
        tags_dict = {
            k: self.tags_dict[k]
            for k in self.tags_position
            if k in self.tags_dict
        }
        new_title = self.build_title(tags_dict)
        return new_title, tags_dict

    @staticmethod
    def audio_language(audio: dict) -> str | None:
        """
        ISO alpha-3 language of an audio track, None when it is not tagged
        """
        for l in audio.get('other_language', []):
            c = ManageTitles.convert_iso(l)
            if c:
                return c[0] if isinstance(c, list) else c
        return None

    @staticmethod
    def channel_count(audio: dict) -> int:
        """
        Number of channels of an audio track, 0 when MediaInfo doesn't tell it (es. '2 / 1' -> 2)
        """
        match = re.match(r'\s*(\d+)', str(audio.get('channel_s') or ''))
        return int(match.group(1)) if match else 0

    @staticmethod
    def audio_score(codec: str, atmos: bool, channel_s: int) -> tuple:
        """
        Sort key of an audio track: codec, then Atmos, then channels
        """
        rank = len(audio_rank) - audio_rank.index(codec) if codec in audio_rank else 0
        return rank, atmos, channel_s

    def is_original_language(self, audio: dict) -> bool:
        codes = [str(code).lower() for code in audio.get('other_language', []) + [audio.get('language') or '']]
        return self.original_language in codes

    def mediainfo_audio(self, category: str) -> dict:
        languages = []
        original_languages = []
        # [(score, label, language, original language)]
        tracks = []
        if self.mediafile.audio_track:
            for audio in self.mediafile.audio_track:
                language = self.audio_language(audio)
                original = self.is_original_language(audio)
                other_format = audio.get('other_format', [])
                if other_format:
                    codec_translated = audio_translate.get(other_format[0], '')
                    if not codec_translated:
                        codec_translated = other_format[0]
                    # Check Atmos
                    dolby = audio.get('commercial_name', "").lower()
                    atmos = 'Atmos' if 'atmos' in dolby else ''
                    # Add audio codec
                    channel_s = self.channel_count(audio)
                    # Add channels
                    ch = audio_channels.get(channel_s, "")
                    tracks.append((self.audio_score(codec_translated, bool(atmos), channel_s),
                                   f"{codec_translated} {ch} {atmos}".strip(), language, original))

                # Add flags
                if language:
                    languages.append(language)
                    if original:
                        original_languages.append(language)
                languages = list(dict.fromkeys(languages))
                # Add multilanguage tag when languages > 2
                if len(languages) > 2:
                    self.tags_dict.update({'multi': 'MULTI'})

        # Best ITA codec + best original language codec, then the tracks with no language up to MAX_AUDIO_CODECS
        best_first = sorted(tracks, key=lambda track: track[0], reverse=True)
        picked = [track for track in best_first if track[2] == "ITA"][:1]
        picked += [track for track in best_first if track[3]][:1]
        picked += [track for track in best_first if track[2] is None]
        audio_codecs = []
        for _, label, _, _ in picked:
            if label not in audio_codecs and len(audio_codecs) < MAX_AUDIO_CODECS:
                audio_codecs.append(label)

        # Flags: ITA, the original language, then the other languages with no codec
        first = [language for language in ["ITA"] + original_languages[:1] if language in languages]
        audio_codecs.extend(dict.fromkeys(first + languages))
        return {category: audio_codecs}

    @staticmethod
    def detect_release_type(tags: list) -> str | None:
        """
        Release type from the source/remux tags: 'encode', 'untouched', 'web' or None when uncertain
        (es. BLURAY alone or no tags)
        """
        tags = {str(tag).upper() for tag in tags}
        if tags & ENCODE_TAGS:
            return "encode"
        if tags & UNTOUCHED_TAGS:
            return "untouched"
        if tags & WEB_TAGS:
            return "web"
        return None

    @staticmethod
    def codec_family_from_name(filename: str, name_encoders: list) -> str | None:
        """
        Codec family ('264' or '265') written in the file name, None if missing or ambiguous
        """
        families = {str(tag)[-3:] for tag in name_encoders}
        for match in NAME_CODEC_PATTERN.finditer(filename):
            if match.group(1):
                families.add(f"26{match.group(1)}")
            elif match.group(2):
                families.add("264")
            else:
                families.add("265")
        families &= {"264", "265"}
        return families.pop() if len(families) == 1 else None

    @staticmethod
    def encoder_signature(video: dict) -> str | None:
        """
        x264/x265 signature left by the encoder in the video track ('264', '265' or None)
        """
        library = str(video.get('writing_library') or '').lower()
        for family in ("264", "265"):
            if f"x{family}" in library:
                return family
        settings = str(video.get('encoding_settings') or '').lower()
        if "cabac=" in settings:
            return "264"
        if "cpuid=" in settings or "ctu=" in settings:
            return "265"
        return None

    @staticmethod
    def normalize_other_codec(video: dict, filename: str) -> str:
        """
        Codecs other than 264/265 (AV1, VP9, VC-1, MPEG-2, XviD...)
        """
        video_format = str(video.get('format') or '')
        if video_format == "MPEG Video":
            version = re.search(r'\d', str(video.get('format_version') or ''))
            return f"MPEG-{version.group(0)}" if version else "MPEG"
        if video_format == "MPEG-4 Visual":
            hint = f"{video.get('codec_id') or ''} {video.get('writing_library') or ''} {filename}".upper()
            if "XVID" in hint:
                return "XviD"
            if "DIVX" in hint or "DX50" in hint:
                return "DivX"
            return "MPEG-4"
        return video_format

    def mediainfo_video(self, category: str) -> dict:
        video = self.mediafile.video_track[0] if self.mediafile.video_track else {}
        video_format = str(video.get('format') or '')
        mediainfo_family = video_family.get(video_format)

        # The file name tells the family, MediaInfo wins when they don't agree
        family = self.name_family
        if video_format:
            if self.name_family and self.name_family != mediainfo_family:
                custom_console.bot_warning_log(
                    f"<> Video codec warning: the file name says {self.name_family} but MediaInfo says"
                    f" '{video_format}'. Using MediaInfo")
            family = mediainfo_family

        if not family:
            if video_format:
                return {category: self.normalize_other_codec(video, self.filename)}
            return {}

        # The encoder in MediaInfo is only a check: it is never read on a WEB-DL
        if self.release_type == "untouched":
            if self.encoder_signature(video):
                custom_console.bot_warning_log(
                    f"<> Warning: possible fake REMUX, the video track was encoded with"
                    f" '{video.get('writing_library') or 'x' + family}'")
            label = "untouched"
        elif self.release_type in ("encode", "web"):
            label = self.release_type
        else:
            label = "encode" if self.encoder_signature(video) else "web"

        return {category: video_codec_labels[label][family]}

    def mediainfo_hdr(self, category: str) -> dict:
        if self.mediafile.video_track:
            for video in self.mediafile.video_track:
                hdr_format_commercial = video.get('hdr_format_commercial', "")
                hdr_format = video.get('hdr_format', "")
                other_hdr_format = video.get('other_hdr_format', "")
                colour_primaries = video.get('color_primaries', "")
                matrix_coefficients = video.get('matrix_coefficients', "")
                bit_depth = video.get('bit_depth', "")
                transfer_characteristics = video.get('transfer_characteristics', "")
                # Check hdr
                if hdr_format_commercial:
                    hdr = ''
                    if hdr_format_commercial.upper() in hdr_map:
                        hdr = hdr_map[hdr_format_commercial.upper()]

                    # if hdr not in hdr_map:
                    if not hdr:
                        custom_console.bot_warning_log(
                            f"<> HDR Warning: '{hdr_format_commercial}' not found in hdr_map")
                    else:
                        custom_console.bot_log(f"Hdr format: '{hdr_format}'")
                        custom_console.bot_log(f"Hdr format commercial: '{hdr_format_commercial}'")

                    if 'DOLBY VISION' in hdr_format_commercial.upper() or 'DOLBY VISION' in hdr_format.upper():
                        # Search for fake remux
                        if any("dvhe.08" in s or "Profile 8" in s for s in other_hdr_format):
                            if self.tags_dict.get('remux', ''):
                                remux = self.tags_dict.get('remux', '')
                                remux.append('HYBRID')
                                self.tags_dict.update({'remux': remux})
                                custom_console.bot_warning_log(
                                    f"<> Warning: HYBRID REMUX with {other_hdr_format}")
                                hdr = f"DOLBY VISION {hdr}"
                                return {category: f"{hdr_map.get(hdr, '*HDR')}"}

                        hdr = f"DOLBY VISION {hdr}"
                    return {category: hdr_map.get(hdr, '*HDR')}
                else:
                    if "2020" in colour_primaries and "2020" in matrix_coefficients:
                        if bit_depth == 10 and transfer_characteristics.strip() == 'PQ':
                            return {category: 'PQ10'}
                        else:
                            custom_console.bot_warning_log(f"<> PQ10 Warning:")
                            custom_console.bot_log(f"colour_primaries: {colour_primaries}")
                            custom_console.bot_log(f"matrix_coefficients: {matrix_coefficients}")
                            custom_console.bot_log(f"bit_depth: |{bit_depth}|")
                            custom_console.bot_log(f"transfer_characteristics: |{transfer_characteristics}|")

        return {}

    def mediainfo_uhd(self, category: str) -> dict:
        """
        identify resolution based on Height and Width tolerance 5%
        """
        mapping = {
            '2160p': 'UHD',
            '1080p': 'FullHD',
            '720p': 'HD',
            '576p': 'SD',
            '480p': 'SD',
        }
        return {
            'resolution': self.media.resolution,
            'uhd': mapping.get(self.media.resolution, 'unknown')
        }

    @staticmethod
    def detect_releaser(name: str, signs_list: dict) -> str:
        """
            normalize both signs_list and base_name
            find the start/end position of the matched sign
            extract the substring from the original base_name
        """
        # Strip the title
        base_name = str(name).strip()

        # sort dictionary from the longest to shortest to avoid partial result (es. 'crew' instead di 'mircrew')
        tokens_signs_list_sorted = sorted(signs_list.keys(), key=len, reverse=True)

        video_exts = [
            "mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "mpeg", "mpg", "m4v", "ts", "3gp"
        ]

        # Regex per catturare l'estensione alla fine (case insensitive)
        pattern = rf"\.({'|'.join(video_exts)})$"

        # # Search for signs in the base_name only at the end of the string
        base_name = re.sub(pattern, "", base_name, flags=re.IGNORECASE)

        # Search for signs in the base_name_normalized
        for token in tokens_signs_list_sorted:
            token = str(token)
            pattern = re.escape(token)
            match = re.search(pattern, base_name, re.IGNORECASE)

            if match:
                # Sign must be the last words
                base_name_len = len(base_name)
                match_len = match.end() - base_name_len
                if match_len == 0:
                    # Capture any characters from the start to the end of base_name
                    sign = base_name[match.start(): match.end()]
                    return f"-{sign}"
        return ""
