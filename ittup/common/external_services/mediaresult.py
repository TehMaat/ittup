# -*- coding: utf-8 -*-

from datetime import datetime

class MediaResult:
    def __init__(self, result=None, video_id: int = 0, imdb_id = None, tvdb_id = None, trailer_key: str = None,
                 keywords_list: str = None, season_title = None, original_language: str = None):
        self.result = result
        self._original_language = original_language
        self.trailer_key = trailer_key
        self.keywords_list = keywords_list
        self.video_id = video_id
        self.imdb_id = imdb_id
        self.tvdb_id = tvdb_id
        self.season_title = season_title
        self.year = None

        if result:
            try:
                self.year = datetime.strptime(result.get_date(), '%Y-%m-%d').year
            except ValueError:
                pass

    @property
    def original_language(self) -> str | None:
        """ TMDB original language (ISO 639-1, es. 'en'), None when unknown """
        # Results cached by older versions have no _original_language
        return (getattr(self, '_original_language', None) or getattr(self.result, 'original_language', None)
                or None)
