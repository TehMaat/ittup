# -*- coding: utf-8 -*-
import hashlib
import os

import diskcache

from ittup.common import config_settings

DAY = 24 * 60 * 60
# The IDs and the data of a movie, a show or a game don't change: they are kept for a month
DEFAULT_EXPIRE = 30 * DAY


class LookupCache:
    """
    Disk cache of the online lookups (TMDB, TVDB, IGDB) in CACHE_PATH/lookups.cache, enabled by CACHE_DBONLINE:
    an upload or a scan repeated on the same contents doesn't send the same requests again
    """

    _cache: diskcache.Cache | None = None
    _pid: int | None = None

    @staticmethod
    def enabled() -> bool:
        return bool(config_settings.user_preferences.CACHE_DBONLINE)

    @classmethod
    def cache(cls) -> diskcache.Cache:
        # Opened in each process: the watcher uploads in a child process
        if cls._cache is None or cls._pid != os.getpid():
            cls._cache = diskcache.Cache(os.path.join(str(config_settings.user_preferences.CACHE_PATH),
                                                      "lookups.cache"))
            cls._pid = os.getpid()
        return cls._cache

    @staticmethod
    def key(*parts) -> str:
        return hashlib.md5(repr(parts).encode("utf-8")).hexdigest()

    @classmethod
    def get(cls, *parts):
        """
        The cached value, None if it is not cached (or the cache is off)
        """
        if not cls.enabled():
            return None
        return cls.cache().get(cls.key(*parts))

    @classmethod
    def set(cls, *parts, value, expire: int = DEFAULT_EXPIRE) -> None:
        if cls.enabled() and value is not None:
            cls.cache().set(cls.key(*parts), value, expire=expire)
