# -*- coding: utf-8 -*-
import json
import os
import re
from datetime import date
from pathlib import Path
from typing import Any

from ittup.view import custom_console


class ManualIds:
    """
    The TMDB IDs typed by the user for the titles that TMDB doesn't find, in a JSON file that can be edited by hand.
    The next upload of the same title (another episode, the same movie) takes the ID from here instead of asking again.
    Key: 'category|normalized title|year' (empty year when the file name has none)
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    @staticmethod
    def normalize(title: str) -> str:
        """ Lower case words: 'Bake.Off.Italia' and 'Bake Off Italia' are the same title """
        return " ".join(re.sub(r"[\W_]+", " ", title).split()).casefold()

    @classmethod
    def key(cls, category: str, title: str, year: int | None) -> str:
        return f"{category}|{cls.normalize(title)}|{year or ''}"

    def load(self) -> dict | None:
        """ The saved IDs; {} when the file doesn't exist, None when it can't be read """
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            custom_console.bot_warning_log(f"The saved TMDB IDs in '{self.path}' can't be read: {error}")
            return None
        if not isinstance(data, dict):
            custom_console.bot_warning_log(f"The saved TMDB IDs in '{self.path}' are not a JSON object")
            return None
        return data

    def get(self, category: str, title: str, year: int | None) -> int | None:
        """
        The TMDB ID saved for the title, None if there is none
        A movie needs the same year. A tv show also matches without the year: the name of an episode often has none
        """
        if not title:
            return None
        data = self.load() or {}
        ids = [self._tmdb_id(data.get(self.key(category, title, year)))]
        if category == "tv":
            if year:
                ids.append(self._tmdb_id(data.get(self.key(category, title, None))))
            else:
                prefix = self.key(category, title, None)
                same_title = {self._tmdb_id(value) for key, value in data.items() if key.startswith(prefix)}
                same_title.discard(None)
                # Two shows with the same title saved with different years: ask
                if len(same_title) == 1:
                    ids.append(same_title.pop())
        return next((tmdb_id for tmdb_id in ids if tmdb_id), None)

    def set(self, category: str, title: str, year: int | None, tmdb_id: int, tmdb_title: str | None = None) -> None:
        """ Save the TMDB ID for the title; a file that can't be read is kept as '.bad' and a new one is written """
        if not title or not tmdb_id:
            return
        data = self.load()
        try:
            if data is None:
                bad = self.path.with_name(f"{self.path.name}.bad")
                os.replace(self.path, bad)
                custom_console.bot_warning_log(f"The unreadable file is kept as '{bad}'")
                data = {}
            data[self.key(category, title, year)] = {"tmdb_id": int(tmdb_id), "title": tmdb_title or title,
                                                     "saved": date.today().isoformat()}
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # Write and rename: the watcher uploads in a child process
            temporary = self.path.with_name(f"{self.path.name}.tmp")
            temporary.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")
            os.replace(temporary, self.path)
        except OSError as error:
            custom_console.bot_warning_log(f"The TMDB ID can't be saved in '{self.path}': {error}")
            return
        custom_console.bot_log(f"TMDB ID {tmdb_id} saved for '{title}': it won't be asked again")

    @staticmethod
    def _tmdb_id(value: Any) -> int | None:
        """ The ID of an entry, None if the entry was edited by hand into something else """
        if isinstance(value, dict):
            value = value.get("tmdb_id")
        try:
            tmdb_id = int(value)
        except (TypeError, ValueError):
            return None
        return tmdb_id if tmdb_id > 0 else None
