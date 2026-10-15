# -*- coding: utf-8 -*-
import os
import re
import hashlib
from datetime import datetime

import diskcache
from typing import TypeVar

from ittup.common.external_services.theMovieDB.core.models.tvshow.alternative import Alternative

from ittup.common.external_services.theMovieDB.core.models.tvshow.translations import Translation
from ittup.common.external_services.theMovieDB.core.models.movie.translations import Translation
from ittup.common.external_services.theMovieDB.core.models.tvshow.details import TVShowDetails
from ittup.common.external_services.theMovieDB.core.models.movie.details import MovieDetails
from ittup.common.external_services.theMovieDB.core.models.movie.nowplaying import NowPlaying
from ittup.common.external_services.theMovieDB.core.models.tvshow.on_the_air import OnTheAir
from ittup.common.external_services.theMovieDB.core.models.tvshow.tvshow import TvShow
from ittup.common.external_services.theMovieDB.core.models.movie.movie import Movie
from ittup.common.external_services.theMovieDB.core.keywords import Keyword
from ittup.common.external_services.theMovieDB.core.videos import Videos
from ittup.common.external_services.mediaresult import MediaResult
from ittup.common.external_services.sessions.session import MyHttp
from ittup.common.external_services.trailers.api import YtTrailer
from ittup.common.external_services.sessions.agents import Agent
from ittup.common.external_services.theMovieDB import config
from ittup.common.external_services.tvdb import TVDB
from ittup.common.lookup_cache import LookupCache, DAY
from ittup.common.utility import ManageTitles

from ittup.core.media import Media
from ittup.core.report import TemporaryFailure
from ittup.view import custom_console

from ittup.core import config_settings

base_url = "https://api.themoviedb.org/3"

# The title ends at the year, the season or the resolution
TITLE_END = re.compile(r"\(?(?<![0-9])(?:19|20)\d{2}(?![0-9])\)?|(?<![a-z0-9])S\d{1,2}(?:E\d+)?(?![a-z0-9])|"
                       r"(?<![0-9])\d{3,4}[pi](?![a-z0-9])", re.IGNORECASE)
ENABLE_LOG = True
T = TypeVar('T')


class MovieEndpoint:
    @staticmethod
    def search(query: str) -> dict:
        return {'url': f'{base_url}/search/movie', 'datatype': Movie, 'query': query, 'results': 'results'}

    @staticmethod
    def playing() -> dict:
        return {'url': f'{base_url}/movie/now_playing', 'datatype': NowPlaying, 'query': '', 'results': 'results'}

    @staticmethod
    def alternative(movie_id: int) -> dict:
        return {'url': f'{base_url}/movie/{movie_id}/alternative_titles', 'datatype': Alternative, 'query': '',
                'results': 'titles'}

    @staticmethod
    def translations(movie_id: int) -> dict:
        return {'url': f'{base_url}/movie/{movie_id}/translations', 'datatype': Translation, 'query': '',
                'results': 'translations'}

    @staticmethod
    def videos(movie_id: int) -> dict:
        return {'url': f'{base_url}/movie/{movie_id}/videos', 'datatype': Videos, 'query': '',
                'results': 'results'}

    @staticmethod
    def details(movie_id: int) -> dict:
        return {'url': f'{base_url}/movie/{movie_id}', 'datatype': MovieDetails, 'query': ''}

    @staticmethod
    def keywords(movie_id: int) -> dict:
        return {'url': f'{base_url}/movie/{movie_id}/keywords', 'datatype': Keyword, 'query': '',
                'results': 'keywords'}

    @staticmethod
    def external_ids(movie_id: int) -> dict:
        return {'url': f'{base_url}/movie/{movie_id}/external_ids', 'datatype': dict, 'query': ''}


class TvEndpoint:
    @staticmethod
    def search(query: str):
        return {'url': f'{base_url}/search/tv', 'datatype': TvShow, 'query': query, 'results': 'results'}

    @staticmethod
    def playing():
        return {'url': f'{base_url}/tv/on_the_air', 'datatype': OnTheAir, 'query': '', 'results': 'results'}

    @staticmethod
    def alternative(serie_id: int) -> dict:
        return {'url': f'{base_url}/tv/{serie_id}/alternative_titles', 'datatype': Alternative, 'query': '',
                'results': 'results'}

    @staticmethod
    def translations(serie_id: int) -> dict:
        return {'url': f'{base_url}/tv/{serie_id}/translations', 'datatype': Translation, 'query': '',
                'results': 'translations'}

    @staticmethod
    def videos(serie_id: int) -> dict:
        return {'url': f'{base_url}/tv/{serie_id}/videos', 'datatype': Videos, 'query': '',
                'results': 'results'}

    @staticmethod
    def details(serie_id: int) -> dict:
        return {'url': f'{base_url}/tv/{serie_id}', 'datatype': TVShowDetails, 'query': ''}

    @staticmethod
    def keywords(serie_id: int) -> dict:
        return {'url': f'{base_url}/tv/{serie_id}/keywords', 'datatype': Keyword, 'query': '',
                'results': 'results'}

    @staticmethod
    def external_ids(serie_id: int) -> dict:
        return {'url': f'{base_url}/tv/{serie_id}/external_ids', 'datatype': dict, 'query': ''}


class TmdbAPI(MyHttp):

    def __init__(self):
        """
        Initialize the Api instance with an HTTP client
        """
        headers = Agent.headers()
        super().__init__(headers)
        self.http_client = self.session

        if config_settings.user_preferences.PREFERRED_LANG.lower() == 'all':
            selected_language = "en-EN"
        else:
            selected_language = config_settings.user_preferences.PREFERRED_LANG

        self.params = {
            "api_key": config.TMDB_APIKEY,
            "language": f"{selected_language.lower()}-{selected_language.upper()}",  # "it-IT",
        }

        # Mappatura automatica degli endpoint
        self.ENDPOINTS = {
            'movie': MovieEndpoint,
            'tv': TvEndpoint,
        }

    def _search(self, query: str, category: str) -> list[T] | None:
        """
        Searches for data based on a query and category
        :param query: search query
        :param category: category of the search query, e.g., 'movie' or 'tv'
        :return: list of T or None
        """
        # Only tv and movie
        if category not in ['movie', 'tv']:
            custom_console.bot_warning_log("Check the category of the search query")
            return []
        if endpoint_class := self.ENDPOINTS.get(category):
            request = endpoint_class.search(query)
            return self.request(endpoint=request)
        else:
            print(f"Endpoint for category '{category}' not found.")
            return []

    def nowplaying(self, category: str) -> list[T] | None:
        """
        Searches for now playing content based on a query and category.
        :param category: category of the now playing content, e.g., 'movie' or 'tv'
        :return: list of T or None
        """

        if endpoint_class := self.ENDPOINTS.get(category):
            request = endpoint_class.playing()
            return self.request(endpoint=request)
        else:
            print(f"Endpoint for category '{category}' not found.")
            return []

    def alternative(self, media_id: int, category: str) -> list[T] | None:
        """
        Searches for data based on a query and category
        :param media_id: id of the media to search for
        :param category: category of the search query, e.g., 'movie' or 'tv'
        :return: list of T or None
        """
        if endpoint_class := self.ENDPOINTS.get(category):
            request = endpoint_class.alternative(media_id)
            return self.request(endpoint=request)
        else:
            print(f"Endpoint for category '{category}' not found.")
            return []

    def translations(self, media_id: int, category: str) -> list[T] | None:
        """
        Searches for data based on a query and category
        :param media_id: id of the media to search for
        :param category: category of the search query, e.g., 'movie' or 'tv'
        :return: list of T or None
        """
        if endpoint_class := self.ENDPOINTS.get(category):
            request = endpoint_class.translations(media_id)
            return self.request(endpoint=request)
        else:
            print(f"Endpoint for category '{category}' not found.")
            return []

    def _videos(self, video_id: int, category: str) -> list[T] | None:
        if endpoint_class := self.ENDPOINTS.get(category):
            request = endpoint_class.videos(video_id)
            return self.request(endpoint=request)
        else:
            print(f"Endpoint for category '{category}' not found.")
            return []

    def details(self, video_id: int, category: str) -> list[T] | None:
        if endpoint_class := self.ENDPOINTS.get(category):
            request = endpoint_class.details(video_id)
            return self.request(endpoint=request)
        else:
            print(f"Endpoint for category '{category}' not found.")
            return []

    def _keywords(self, video_id: int, category: str) -> list[T] | None:
        if endpoint_class := self.ENDPOINTS.get(category):
            request = endpoint_class.keywords(video_id)
            return self.request(endpoint=request)
        else:
            print(f"Endpoint for category '{category}' not found.")
            return []

    def find_by_imdb(self, imdb_id: int, category: str) -> int | None:
        """ Return the TMDB ID of the movie or tv show that matches the IMDB ID """
        if category not in ['movie', 'tv']:
            return None
        request = {'url': f'{base_url}/find/tt{int(imdb_id):07d}', 'datatype': dict, 'query': '',
                   'params': {'external_source': 'imdb_id'}}
        response = self.request(endpoint=request)
        if response:
            results = response[0].get(f'{category}_results', [])
            if results:
                return results[0].get('id')
        return None

    def original_language(self, video_id: int, category: str) -> str | None:
        """ Original language (ISO 639-1) of the movie or tv show """
        if endpoint_class := self.ENDPOINTS.get(category):
            request = {**endpoint_class.details(video_id), 'datatype': dict}
            response = self.request(endpoint=request)
            if response:
                return response[0].get('original_language') or None
        return None

    def italian_details(self, video_id: int, category: str) -> dict | None:
        """ Details of the movie or tv show in Italian (title, seasons..), whatever the preferred language """
        if not video_id:
            return None
        if endpoint_class := self.ENDPOINTS.get(category):
            # The details of a show change with its new episodes (next_episode_to_air): cached for a day
            request = {**endpoint_class.details(video_id), 'datatype': dict, 'params': {'language': 'it-IT'},
                       'expire': DAY}
            response = self.request(endpoint=request)
            if response:
                return response[0]
        return None

    def external_ids(self, video_id: int, category: str) -> dict | None:
        if endpoint_class := self.ENDPOINTS.get(category):
            request = endpoint_class.external_ids(video_id)
            response = self.request(endpoint=request)
            if response:
                return response[0]  # è un singolo dict, non una lista
        return None

    def request(self, endpoint: dict) -> list[T] | None:
        """
        Sends a request to the API and returns a list of instances of the specified 'datatype'.
        :param endpoint: request endpoint
        :return: list of T or None
        """
        params = {**self.params, "query": endpoint['query'], **endpoint.get('params', {})}

        # The same request in a repeated upload or scan is read from the cache (CACHE_DBONLINE)
        cache_key = ("tmdb", endpoint['url'], sorted((k, str(v)) for k, v in params.items() if k != "api_key"))
        response_data = LookupCache.get(*cache_key)
        if response_data is not None:
            return [endpoint['datatype'](**attribute) for attribute in response_data]

        response = self.get_url(endpoint['url'], params=params)

        if response:
            if response.status_code == 200:
                if not endpoint.get('results', None):
                    response_data = [response.json()]
                else:
                    response_data = response.json().get(endpoint['results'], [])

                # An empty search is not cached: TMDB may add the movie later
                if response_data:
                    LookupCache.set(*cache_key, value=response_data, expire=endpoint.get('expire', 30 * DAY))
                return [endpoint['datatype'](**attribute) for attribute in response_data]
            else:
                return []
        return None


class DbOnline(TmdbAPI):
    def __init__(self, media: Media, category: str, no_title: str) -> None:
        super().__init__()
        self.media = media
        self.query = media.guess_title
        self.category = category
        self.imdb_id = None
        self.tvdb_id = None
        self.no_title = no_title
        self.relaxed_year = False

        # Load the cache file
        self.cache = None
        if config_settings.user_preferences.CACHE_DBONLINE:
            self.cache = diskcache.Cache(str(os.path.join(config_settings.user_preferences.CACHE_PATH, "tmdb.cache")))

        if media.tmdb_id or media.imdb_id or media.tvdb_id:
            # Skip cache if there is a tmdb id or imdb in the title string
            self.media_result = self.results_in_string(tmdb_id=int(media.tmdb_id or 0),
                                                       imdb_id=int(media.imdb_id or 0),
                                                       tvdb_id=int(media.tvdb_id or 0))
        else:
            # Load from the cache or search online for a tmdb id or imdb
            # Search for a video based on the filename or the title from the -notitle flag in the CLI
            if no_title:
                self.query = no_title
            self.media_result = self.search()

    @staticmethod
    def hash_key(key: str) -> str:
        """ Generate a hashkey for the cache index """
        return hashlib.md5(key.encode('utf-8')).hexdigest()

    def is_like(self, results: list[T]) -> T | bool:
        if results:
            # Cache alternative_titles/translations per result id: one request each per search
            alternatives_cache = {}
            translations_cache = {}

            def get_alternatives(media_id: int) -> list[T] | None:
                if media_id not in alternatives_cache:
                    alternatives_cache[media_id] = self.alternative(media_id=media_id, category=self.category)
                return alternatives_cache[media_id]

            def get_translations(media_id: int) -> list[T] | None:
                if media_id not in translations_cache:
                    translations_cache[media_id] = self.translations(media_id=media_id, category=self.category)
                return translations_cache[media_id]

            tmdb_debug = config_settings.user_preferences.TMDB_DEBUG

            # Search for in the tile or original_name
            for result in results:
                if tmdb_debug:
                    self.debug_scores(result, get_alternatives(result.id), get_translations(result.id))

                # check date
                if not self.year_matches(result):
                    continue

                # Search for title
                if ManageTitles.fuzzyit(str1=ManageTitles.clean_text(self.query),
                                        str2=ManageTitles.clean_text(result.get_title())) > 95:
                    return result

                if ManageTitles.fuzzyit(str1=ManageTitles.clean_text(self.query),
                                        str2=ManageTitles.clean_text(result.get_original())) > 95:
                    return result

            # Search for alternative title
            for result in results:
                alternative = get_alternatives(result.id)
                if alternative:
                    for alt in alternative:
                        if ManageTitles.fuzzyit(str1=self.query, str2=alt.title) > 95:
                            return result

            for result in results:
                translations = get_translations(result.id)
                if translations:
                    for tr in translations:
                        if tr.data:
                            title = tr.data.name or tr.data.title
                            if title:
                                if ManageTitles.fuzzyit(self.query, title) > 95:
                                    return result

            # Search for a mixed title: localized title plus words of the main title
            # e.g. 'Hellboy Animated La Spada Maledetta'
            for result in results:
                if not self.year_matches(result):
                    continue
                main_titles = [result.get_title(), result.get_original()]
                local_titles = [alt.title for alt in get_alternatives(result.id) or [] if alt.title]
                for tr in get_translations(result.id) or []:
                    if tr.data and (tr.data.name or tr.data.title):
                        local_titles.append(tr.data.name or tr.data.title)
                for title in local_titles:
                    if ManageTitles.is_mixed_title(query=self.query, local_title=title, main_titles=main_titles):
                        return result
        return False

    def year_matches(self, result: T) -> bool:
        """
        False only when both years are known and they differ
        With relaxed_year a movie may differ by one year and a tv show may have the year of a later season
        """
        if result.get_date() and self.media.guess_filename.guessit_year:
            tmdb_year = datetime.strptime(result.get_date(), '%Y-%m-%d').year
            year = self.media.guess_filename.guessit_year
            if not self.relaxed_year:
                return tmdb_year == year
            if self.category == 'tv':
                return year >= tmdb_year - 1
            return abs(tmdb_year - year) <= 1
        return True

    def debug_scores(self, result: T, alternatives: list[T] | None, translations: list[T] | None) -> None:
        """ Log the fuzzy score of every TMDB title candidate (TMDB_DEBUG) """
        query = ManageTitles.clean_text(self.query)
        custom_console.bot_warning_log(f"TMDB title: '{result.get_title()}' score: "
                                       f"{ManageTitles.fuzzyit(str1=query, str2=ManageTitles.clean_text(result.get_title()))}")
        custom_console.bot_warning_log(f"TMDB original: '{result.get_original()}' score: "
                                       f"{ManageTitles.fuzzyit(str1=query, str2=ManageTitles.clean_text(result.get_original()))}")
        if alternatives:
            for a in alternatives:
                custom_console.bot_warning_log(f"Alt title: '{a.title}' score: "
                                               f"{ManageTitles.fuzzyit(str1=self.query, str2=a.title)}")
        if translations:
            for t in translations:
                if t.data:
                    title = t.data.name or t.data.title
                    if title:
                        custom_console.bot_warning_log(f"Translation: '{title}' score: "
                                                       f"{ManageTitles.fuzzyit(str1=self.query, str2=title)}")

    def results_in_string(self, tmdb_id: int, imdb_id: int, tvdb_id: int) -> MediaResult:
        """
        Use id from the string filename or name folder
        Cache disabled
        """
        keywords_list = ''
        trailer_key = ''
        self.imdb_id = imdb_id or None
        self.tvdb_id = tvdb_id or None

        # Only the IMDB ID in the title string: ask TMDB for the matching TMDB ID
        if not tmdb_id and imdb_id:
            tmdb_id = self.find_by_imdb(imdb_id=imdb_id, category=self.category) or 0
            if not tmdb_id:
                custom_console.bot_warning_log(f"TMDB ID not found for IMDB ID '{imdb_id}'")

        original_language = None
        if tmdb_id > 0:
            original_language = self.original_language(video_id=tmdb_id, category=self.category)
            # Fill the IDs missing from the title string
            self.add_external_ids(tmdb_id)
            # Request trailer and keywords
            trailer_key = self.trailer(tmdb_id)
            keywords_list = self.keywords(tmdb_id) if trailer_key else ''

        search_results = MediaResult(video_id=tmdb_id, imdb_id=self.imdb_id, tvdb_id=self.tvdb_id,
                                     trailer_key=trailer_key, keywords_list=keywords_list,
                                     original_language=original_language)
        self.print_results(results=search_results)
        return search_results

    def search(self) -> MediaResult | None:
        """
        Search for results based on a tmdb query
        season: True = search for a season. Title unknown
        """
        # The same title is another movie in another year, or a tv show
        cache_key = self.hash_key(f"{self.category}|{self.media.guess_filename.guessit_year}|{self.query}")

        # Search in the cache first if cache is enabled
        if config_settings.user_preferences.CACHE_DBONLINE:
            search_results = self.load_cache(cache_key)
            if search_results:
                # Results cached by older versions may lack the IMDB ID
                if search_results.video_id and not search_results.imdb_id:
                    self.imdb_id = None
                    self.tvdb_id = search_results.tvdb_id
                    self.add_external_ids(search_results.video_id)
                    if self.imdb_id:
                        search_results.imdb_id = self.imdb_id
                        search_results.tvdb_id = self.tvdb_id
                        self.cache[cache_key] = search_results
                self.print_results(results=search_results)
                return search_results

        # or start an on-line search
        result, results = self.search_queries()

        # Use imdb_id when tmdb_id is not available
        tvdb_result = self.tvdb_search()
        if tvdb_result:
            self.tvdb_id = tvdb_result.get('tvdb_id', None)
            self.imdb_id = tvdb_result.get('imdb_id', None)

        if results:
            if result:
                # Get the trailer
                trailer_key = self.trailer(result.id)
                keywords_list = self.keywords(result.id)

                # TMDB external_ids as override: only override if the field is present
                self.add_external_ids(result.id, override=True)

                search_results = MediaResult(result, video_id=result.id, imdb_id=self.imdb_id, tvdb_id=self.tvdb_id,
                                             trailer_key=trailer_key, keywords_list=keywords_list)

                self.print_results(results=search_results)
                # Write to the cache if it is enabled
                if config_settings.user_preferences.CACHE_DBONLINE:
                    self.cache[cache_key] = search_results
                # return the result
                return search_results

        # No response from TMDB
        if results is None:
            custom_console.bot_error_log(
                f"TMDB - No response from the remote host or the API key is invalid. Retry or update your key")
            raise TemporaryFailure("TMDB - No response from the remote host or the API key is invalid")

        # not results found so try to initialize imdb
        custom_console.bot_warning_log(f"Title not found.What the bot has understood:")

        custom_console.bot_warning_log(f"Title:   '{self.query}'\ncategory:'{self.category}'")
        if self.category in 'tv':
            serie = f"S{str(self.media.guess_season).zfill(2)}" if self.media.guess_season else ''
            if not self.media.torrent_pack:
                serie += f"E{str(self.media.guess_episode).zfill(2)}"
            custom_console.bot_warning_log(f"details: '{serie}' Pack: '{self.media.torrent_pack}'")

        # Ask User TMDB ID
        search_results = self.manual_search()
        # Don't cache a skipped result (TMDB ID 0): the next run should search again
        if config_settings.user_preferences.CACHE_DBONLINE and search_results and search_results.video_id:
            self.cache[cache_key] = search_results
        return search_results

    def search_queries(self) -> tuple[T | None, list[T] | None]:
        """
        Search TMDB with the title from the file name, then with the other titles written in the name
        (es. '(500) Days of Summer', the title in parentheses). Each query is checked first with the exact year,
        then with a tolerance (movies released at the end of the year, the year of a season..)
        Returns the result found and the results of the first query (None if TMDB doesn't answer)
        On success self.query is the query that found the result, otherwise the first query
        """
        queries = [self.query] if self.no_title else self.title_queries(self.query, self.media.title)
        responses = {}
        for relaxed in (False, True):
            self.relaxed_year = relaxed
            for query in queries:
                if query not in responses:
                    responses[query] = self._search(query, self.category)
                    # No response from TMDB
                    if responses[query] is None:
                        if query == queries[0]:
                            return None, None
                        responses[query] = []
                self.query = query
                result = self.is_like(responses[query]) if responses[query] else None
                if result:
                    if query != queries[0] or relaxed:
                        custom_console.bot_log(f"TMDB: found with the title '{query}'"
                                               f"{' and a year tolerance' if relaxed else ''}")
                    self.relaxed_year = False
                    return result, responses[query]
        self.relaxed_year = False
        self.query = queries[0]
        return None, responses[queries[0]]

    @staticmethod
    def title_queries(query: str, name: str) -> list[str]:
        """
        TMDB queries: the title from guessit, then the name before the year, the season or the resolution,
        and the titles in parentheses ('Lo Chiamavano Jeeg Robot (They Call Me Jeeg) (2015)')
        """
        queries = [query]
        name = re.sub(r"\.(mkv|mp4|avi|m2ts|ts|mov|wmv|m4v|mpg|mpeg|webm)$", "", name, flags=re.IGNORECASE)
        # Dots and underscores as spaces, but not in the acronyms (S.W.A.T.)
        name = re.sub(r"(?<=[^\W\d_]{2})[._]|[._](?=[^\W\d_]{2})|_", " ", name)
        prefix = TITLE_END.split(name, maxsplit=1)[0]
        prefix = re.sub(r"[\[{].*", "", prefix).strip(" -.")
        # Titles in parentheses, not numbers like '(500)'
        groups = [group for group in re.findall(r"\(([^()]+)\)", prefix) if re.search(r"[^\W\d_]{2}", group)]
        # The whole prefix, e.g. '(500) Days of Summer'
        queries.append(re.sub(r"[()]", "", prefix))
        # The prefix without the parentheses and each title in parentheses
        queries.append(re.sub(r"\([^()]*\)", "", prefix))
        queries.extend(groups)

        unique = []
        for item in queries:
            item = re.sub(r"\s+", " ", item or "").strip(" -.")
            if item and item.lower() not in [u.lower() for u in unique]:
                unique.append(item)
        return unique[:4]

    def add_external_ids(self, video_id: int, override: bool = False) -> None:
        """ Set the IMDB and TVDB IDs from TMDB; override=False keeps the ones already known """
        ext = self.external_ids(video_id=video_id, category=self.category)
        if ext:
            if ext.get('imdb_id') and (override or not self.imdb_id):
                self.imdb_id = int(ext['imdb_id'].replace('tt', ''))
            if ext.get('tvdb_id') and (override or not self.tvdb_id):
                self.tvdb_id = ext['tvdb_id']

    def tvdb_search(self) -> dict | None:
        tvdb = TVDB(category=self.category)
        return tvdb.search(query=self.query, query_year=self.media.guess_filename.guessit_year)

    def manual_search(self) -> MediaResult | None:
        """
                 User digits valid TMDB id or wait
                 User digits 0 if he wants to search on IMDB
                 Returns:
                     MediaResult
        """
        user_id = 0
        while True:
            # Check if user wants to skip
            if not config_settings.user_preferences.SKIP_TMDB:
                try:
                    user_id = custom_console.user_input(message=f"Please digit a valid TMDB ID (0=skip)->")
                except KeyboardInterrupt:
                    custom_console.bot_error_log("\nOperation cancelled")
                    exit(0)
            else:
                custom_console.bot_warning_log(f"\n ** Auto skip TMDB ID **\n")

            # Try to add IMDB ID if tmdb is not available
            if user_id == 0:
                # try searching for a YouTube video anyway
                trailer_key = self.youtube_trailer()
                search_results = MediaResult(video_id=user_id, imdb_id=self.imdb_id, trailer_key=trailer_key,
                                             keywords_list='not available')
                self.print_results(results=search_results)
                return search_results
            else:
                result = self.search_id(video_id=user_id)
                if result:
                    # The TVDB search may have missed: take the IMDB ID from TMDB
                    self.add_external_ids(user_id, override=True)
                    # Request trailer and keywords
                    trailer_key = self.trailer(user_id)
                    keywords_list = self.keywords(user_id) if trailer_key else ''
                    search_results = MediaResult(result=result, video_id=user_id, imdb_id=self.imdb_id,
                                                 tvdb_id=self.tvdb_id, trailer_key=trailer_key,
                                                 keywords_list=keywords_list)
                    self.print_results(results=search_results)
                    return search_results

    def youtube_trailer(self) -> str | None:
        # Search trailer on YouTube
        if 'no_key' in config_settings.tracker_config.YOUTUBE_KEY:
            return "not available"

        if config_settings.user_preferences.SKIP_YOUTUBE:
            return "Skipped"

        yt_trailer = YtTrailer(self.query)
        result = yt_trailer.get_trailer_link()
        if result:
            for r in result:
                title = r.items[0].snippet.title if r.items else None
                if self.query in title:
                    return r.items[0].id.videoId
            return "not available"
        else:
            user_youtube_id = custom_console.user_input_str(message="Sorry trailer not found."
                                                                    " Please digit a valid Youtube ID (0=skip)->")
            if user_youtube_id == 0:
                return "not available"
            return user_youtube_id

    def trailer(self, video_id: int) -> str | None:
        # Search for tmdb trailer
        trailers = self._videos(video_id, self.category)
        if trailers:
            trailer = next((video for video in trailers if video.site.lower() == 'youtube'), None)
            if trailer:
                return trailer.key
            else:
                return "not available"

        # Search for YouTube trailer
        return self.youtube_trailer()

    def keywords(self, video_id: int) -> str | None:
        keywords_list = self._keywords(video_id, self.category)
        if keywords_list:
            return ",".join([key.name for key in keywords_list])
        else:
            return "not available"

    def print_results(self, results: MediaResult) -> None:
        custom_console.bot_log(f"'TMDB TITLE'..... {self.query}")
        custom_console.bot_log(f"'TMDB ID'........ {results.video_id}")
        if results.imdb_id:
            custom_console.bot_warning_log(f"'IMDB ID'........ '{results.imdb_id}'")
        if results.tvdb_id:
            custom_console.bot_warning_log(f"'TVDB ID'........ '{results.tvdb_id}'")
        custom_console.bot_log(f"'TMDB KEYWORDS'.. {results.keywords_list}")
        if results.trailer_key.upper() in  ['SKIPPED', 'NOT AVAILABLE']:
            custom_console.bot_log(f"'TRAILER' ....... {results.trailer_key}")
        else:
            custom_console.bot_log(f"'TRAILER' ....... https://www.youtube.com/watch?v={results.trailer_key}")

    def load_cache(self, query: str) -> MediaResult | None:
        # Check if the item is in the cache
        if query not in self.cache:
            return None

        custom_console.bot_warning_log(f"<> Using cached results")
        try:
            # Try to get the video from the cache
            return self.cache[query]
        except KeyError:
            # Handle the case where the video is missing or the cache is corrupted
            custom_console.bot_error_log("Cached frame not found or cache file corrupted")
            custom_console.bot_error_log("Proceed to extract the screenshot again. Please wait..")
            return None

    def search_id(self, video_id: int) -> list[T] | None:
        """
                 Search Movie or Tvshow based on ID
                 Build a DataClass for the MediaResult
                 Returns:
                     list[T]: generic Movie or Tvshow results
        """
        result = self.details(video_id=video_id, category=self.category)
        if result:
            return result[0]
        return None
