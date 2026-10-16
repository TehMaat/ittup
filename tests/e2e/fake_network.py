# -*- coding: utf-8 -*-
"""
Fake network for the end-to-end tests: every httpx and requests call is answered here,
so ITTup runs on the dummy files without the tracker, TMDB or the image hosts.

urllib (the TVDB library) is answered too, and any other connection to the internet fails:
a new service shows up as an error instead of reaching the real one.

Each request is written to the JSON lines file in ITTUP_E2E_REQUESTS, for the test assertions.
A request with no route gets a 404 and is logged with "unmatched": true
"""
import io
import json
import os
import re
import socket
import urllib.error
import urllib.request
from urllib.parse import urlsplit, parse_qsl

import httpx
import requests

TRACKER_HOST = "tracker.test"

# TMDB ids of the dummy contents
MOVIE_ID = 550
TV_ID = 1399

MOVIE = {"id": MOVIE_ID, "title": "Dummy Movie", "original_title": "Dummy Movie", "original_language": "en",
         "release_date": "2020-05-01", "overview": "A dummy movie.", "poster_path": "/poster.jpg",
         "backdrop_path": "/backdrop.jpg", "genre_ids": [18], "popularity": 10.0, "vote_average": 7.0,
         "vote_count": 100, "adult": False, "video": False}

TV = {"id": TV_ID, "name": "Dummy Show", "original_name": "Dummy Show", "original_language": "en",
      "first_air_date": "2019-04-01", "overview": "A dummy show.", "poster_path": "/poster.jpg",
      "backdrop_path": "/backdrop.jpg", "genre_ids": [18], "popularity": 10.0, "vote_average": 7.0,
      "vote_count": 100, "origin_country": ["US"]}

MOVIE_DETAILS = {**MOVIE, "title": "Film Finto", "imdb_id": "tt0137523", "runtime": 1, "status": "Released",
                 "genres": [{"id": 18, "name": "Dramma"}], "tagline": "", "belongs_to_collection": None,
                 "budget": 0, "revenue": 0, "homepage": "", "spoken_languages": [], "production_companies": [],
                 "production_countries": [], "origin_country": ["US"]}

TV_DETAILS = {**TV, "name": "Serie Finta", "status": "Ended", "in_production": False, "number_of_seasons": 1,
              "number_of_episodes": 10, "genres": [{"id": 18, "name": "Dramma"}], "tagline": "",
              "last_air_date": "2019-06-01", "next_episode_to_air": None, "type": "Scripted",
              "seasons": [{"season_number": 1, "episode_count": 10, "air_date": "2019-04-01", "id": 1,
                           "name": "Stagione 1", "overview": "", "poster_path": None}],
              "episode_run_time": [1], "languages": ["en"], "networks": [], "production_companies": [],
              "production_countries": [], "spoken_languages": [], "created_by": [], "homepage": ""}


# The torrent downloaded from the tracker after the upload
DUMMY_TORRENT = b"d8:announce20:https://tracker.test4:infod6:lengthi1e4:name5:dummy12:piece lengthi16384e6:pieces20:" \
                + b"\0" * 20 + b"ee"


def page(results: list) -> dict:
    return {"page": 1, "results": results, "total_pages": 1, "total_results": len(results)}


def tmdb(path: str, params: dict):
    if path == "/3/search/movie":
        return 200, page([MOVIE])
    if path == "/3/search/tv":
        return 200, page([TV])
    if re.fullmatch(r"/3/find/tt\d+", path):
        return 200, {"movie_results": [MOVIE], "tv_results": [], "person_results": []}
    match = re.fullmatch(r"/3/(movie|tv)/(\d+)(/[a-z_]+)?", path)
    if match:
        category, _, endpoint = match.groups()
        if endpoint is None:
            return 200, MOVIE_DETAILS if category == "movie" else TV_DETAILS
        if endpoint == "/external_ids":
            return 200, {"id": int(match.group(2)), "imdb_id": "tt0137523", "tvdb_id": 121361}
        if endpoint == "/keywords":
            return 200, {"id": int(match.group(2)), "keywords": [{"id": 1, "name": "dummy"}],
                         "results": [{"id": 1, "name": "dummy"}]}
        if endpoint == "/videos":
            return 200, {"id": int(match.group(2)), "results": [
                {"key": "dQw4w9WgXcQ", "site": "YouTube", "type": "Trailer", "name": "Trailer", "iso_639_1": "it",
                 "iso_3166_1": "IT", "official": True, "id": "1", "size": 1080,
                 "published_at": "2020-01-01T00:00:00.000Z"}]}
        if endpoint == "/alternative_titles":
            return 200, {"id": int(match.group(2)), "titles": [], "results": []}
        if endpoint == "/translations":
            return 200, {"id": int(match.group(2)), "translations": []}
    if path in ("/3/movie/now_playing", "/3/tv/on_the_air"):
        return 200, page([])
    return None


def tracker(method: str, path: str, params: dict):
    if path == "/api/torrents/filter":
        return 200, {"data": [], "links": {"next": None}, "meta": {"current_page": 1, "last_page": 1}}
    if path == "/api/torrents/upload" and method == "POST":
        return 200, {"success": True, "data": f"https://{TRACKER_HOST}/torrent/download/1.abcdef",
                     "message": "Torrent uploaded successfully."}
    if path.startswith("/torrent/download/"):
        return 200, DUMMY_TORRENT
    if path == "/api/torrents":
        return 200, {"data": [], "links": {"next": None}, "meta": {"current_page": 1, "last_page": 1}}
    return None


def tvdb(path: str):
    if path == "/v4/login":
        return 200, {"status": "success", "data": {"token": "e2e_token"}}
    if path == "/v4/search":
        return 200, {"status": "success", "data": []}
    return None


def image_host(host: str):
    image = f"https://{host}/images/dummy.png"
    return 200, {"status_code": 200, "success": {"code": 200}, "status": 200,
                 "image": {"url": image, "display_url": image, "medium": {"url": image}, "thumb": {"url": image}},
                 "data": {"url": image, "display_url": image, "medium": {"url": image}, "thumb": {"url": image}}}


def route(method: str, url: str, form: dict | None = None) -> tuple[int, object | bytes]:
    parts = urlsplit(url)
    params = dict(parse_qsl(parts.query))
    answer = None
    if parts.hostname == "api.themoviedb.org":
        answer = tmdb(parts.path, params)
    elif parts.hostname == TRACKER_HOST:
        answer = tracker(method, parts.path, params)
    elif parts.hostname == "api4.thetvdb.com":
        answer = tvdb(parts.path)
    elif parts.path.endswith("/api/1/upload") or parts.hostname == "api.imgbb.com":
        answer = image_host(parts.hostname)
    elif parts.hostname == "image.tmdb.org":
        answer = 200, b"\x89PNG\r\n\x1a\n"
    elif parts.hostname == "pypi.org":
        # The update check at startup: no newer version
        answer = 200, {"info": {"version": "0.0.0"}}
    log(method, url, unmatched=answer is None, form=form)
    return answer or (404, {"message": "no route in the e2e fake network"})


def log(method: str, url: str, unmatched: bool, form: dict | None = None) -> None:
    path = os.environ.get("ITTUP_E2E_REQUESTS")
    if path:
        with open(path, "a", encoding="utf-8") as requests_log:
            requests_log.write(json.dumps({"method": method, "url": url, "unmatched": unmatched,
                                           "form": form or {}}) + "\n")


def form_fields(content: bytes | str | None) -> dict:
    """ The text fields of a multipart form, e.g. the title and the description sent to the tracker """
    if isinstance(content, str):
        content = content.encode()
    if not content:
        return {}
    fields = re.findall(rb'name="([^"]+)"\r\n\r\n(.*?)\r\n--', content, re.S)
    return {name.decode(): value.decode(errors="replace") for name, value in fields}


def body(answer: object | bytes) -> tuple[bytes, dict]:
    if isinstance(answer, bytes):
        return answer, {"content-type": "image/png"}
    return json.dumps(answer).encode(), {"content-type": "application/json"}


def fake_httpx_send(self, request: httpx.Request, **kwargs) -> httpx.Response:
    status_code, answer = route(request.method, str(request.url), form_fields(request.read()))
    content, headers = body(answer)
    return httpx.Response(status_code, content=content, headers=headers, request=request)


def fake_requests_send(self, request: requests.PreparedRequest, **kwargs) -> requests.Response:
    status_code, answer = route(request.method, request.url, form_fields(request.body))
    content, headers = body(answer)
    response = requests.Response()
    response.status_code = status_code
    response._content = content
    response.headers.update(headers)
    response.url = request.url
    response.request = request
    response.encoding = "utf-8"
    return response


class FakeUrllibResponse(io.BytesIO):
    def __init__(self, status: int, content: bytes):
        super().__init__(content)
        self.status = status

    def getcode(self) -> int:
        return self.status


def fake_urlopen(request, data=None, **kwargs) -> FakeUrllibResponse:
    if isinstance(request, str):
        request = urllib.request.Request(request, data=data)
    if data is not None and request.data is None:
        request.data = data
    status_code, answer = route(request.get_method(), request.full_url)
    content, _ = body(answer)
    if status_code >= 400:
        raise urllib.error.HTTPError(request.full_url, status_code, "e2e fake network", {}, io.BytesIO(content))
    return FakeUrllibResponse(status_code, content)


real_connect = socket.socket.connect


def no_internet_connect(self, address):
    # Local sockets (the ffmpeg pipes, a local torrent client) are fine, the internet is not
    if self.family in (socket.AF_INET, socket.AF_INET6) and address[0] not in ("127.0.0.1", "::1", "localhost"):
        raise ConnectionRefusedError(f"e2e tests: no internet, connection to {address} blocked")
    return real_connect(self, address)


def install() -> None:
    httpx.Client.send = fake_httpx_send
    requests.Session.send = fake_requests_send
    urllib.request.urlopen = fake_urlopen
    socket.socket.connect = no_internet_connect
