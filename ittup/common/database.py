import json
import os
import sqlite3
from ittup.core import config_settings

# Torrent attributes
create_table_sql = ('\n'
                    'CREATE TABLE IF NOT EXISTS torrents (\n'
                    '    id INTEGER PRIMARY KEY AUTOINCREMENT,\n'
                    '    name TEXT,\n'
                    '    category TEXT,\n'
                    '    category_id INTEGER,\n'
                    '    created_at TEXT,\n'
                    '    description TEXT,\n'
                    '    details_link TEXT,\n'
                    '    download_link TEXT,\n'
                    '    double_upload BOOLEAN,\n'
                    '    featured BOOLEAN,\n'
                    '    freeleech TEXT,\n'
                    '    igdb_id INTEGER,\n'
                    '    imdb_id TEXT,\n'
                    '    info_hash TEXT,\n'
                    '    internal BOOLEAN,\n'
                    '    leechers INTEGER,\n'
                    '    magnet_link TEXT,\n'
                    '    mal_id INTEGER,\n'
                    '    media_info TEXT,\n'
                    '    release_year INTEGER,\n'
                    '    resolution TEXT,\n'
                    '    resolution_id INTEGER,\n'
                    '    seeders INTEGER,\n'
                    '    size INTEGER,\n'
                    '    times_completed INTEGER,\n'
                    '    tmdb_id INTEGER,\n'
                    '    tvdb_id INTEGER,\n'
                    '    type TEXT,\n'
                    '    type_id INTEGER,\n'
                    '    uploader TEXT,\n'
                    '    personal_release BOOLEAN,\n'
                    '    refundable BOOLEAN,\n'
                    '    num_file INTEGER,\n'
                    '    bd_info TEXT,\n'
                    '    genres TEXT,\n'
                    '    poster TEXT,\n'
                    '    meta TEXT,\n'
                    '    files TEXT\n'
                    ')\n')


class Database:
    """
    Create a new database and populate it with torrents attributes
    Search torrents based on attributes

    The file is opened, and the table created again, at the first write: only -db and -dump save the
    search results, so a duplicate check or a search never touches it (#156). Another ITTup process
    that holds it, or a CACHE_PATH where SQLite can't lock, made every upload fail with "database is locked"
    """

    # Seconds to wait for another process that holds the file before 'database is locked' (SQLite waits 5)
    TIMEOUT = 30

    def __init__(self, db_file: str) -> None:
        self.filename = db_file
        self.CACHE_PATH = config_settings.user_preferences.CACHE_PATH
        self.database: sqlite3.Connection | None = None
        self.cursor: sqlite3.Cursor | None = None

    def connect(self) -> sqlite3.Cursor:
        """
        Opens the file and creates the table again the first time it is called
        """
        if self.cursor is None:
            self.database = sqlite3.connect(os.path.join(self.CACHE_PATH, f"{self.filename}.db"),
                                            timeout=self.TIMEOUT)
            self.cursor = self.database.cursor()
            self.build()
        return self.cursor

    def build(self) -> None:
        assert self.database is not None and self.cursor is not None
        self.cursor.execute("DROP TABLE IF EXISTS torrents")
        self.cursor.execute(create_table_sql)
        self.database.commit()

    def write(self, data: dict) -> None:
        cursor = self.connect()
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                data[key] = json.dumps(value)

        keys = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        values = tuple(data.values())
        sql = f'''INSERT INTO torrents ({keys}) VALUES ({placeholders})'''
        cursor.execute(sql, values)
        assert self.database is not None
        self.database.commit()

    def close(self) -> None:
        if self.database is not None:
            self.database.close()
        self.database = None
        self.cursor = None
