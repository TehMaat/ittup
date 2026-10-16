# -*- coding: utf-8 -*-
import argparse
import os
import json

import pytest

from ittup.core.bot import Bot, run_outcome
from ittup.core.report import report, TemporaryFailure, TEMPORARY_FAILURE
from ittup.core.watcher_queue import UploadQueue, RunOutcome, quarantine


def test_the_queue_is_kept_across_restarts(tmp_path):
    movie = tmp_path / "Movie.mkv"
    movie.write_bytes(b"x")
    queue_file = tmp_path / "queue.json"

    queue = UploadQueue(queue_file)
    queue.add(str(movie))
    queue.add(str(movie))
    queue.add(str(tmp_path / "Deleted.mkv"))
    assert len(json.loads(queue_file.read_text())) == 2

    # After a restart: the deleted entry is dropped
    resumed = UploadQueue(queue_file)
    assert [entry.path for entry in resumed.entries] == [str(movie)]


def test_exponential_backoff(tmp_path):
    assert [UploadQueue.backoff(attempts) for attempts in range(1, 9)] == [60, 120, 240, 480, 960, 1920, 3600, 3600]
    movie = tmp_path / "Movie.mkv"
    movie.write_bytes(b"x")
    queue = UploadQueue(tmp_path / "queue.json")
    queue.add(str(movie))
    entry = queue.entries[0]
    assert queue.retry(entry, "network error", now=1000) == 60
    assert queue.due(now=1059) == []
    assert queue.due(now=1060) == [entry]
    assert queue.retry(entry, "network error", now=2000) == 120
    saved = json.loads((tmp_path / "queue.json").read_text())[0]
    assert (saved["attempts"], saved["next_attempt"], saved["last_error"]) == (2, 2120, "network error")


def test_quarantine(tmp_path):
    folder = tmp_path / "destination" / "Show S01"
    folder.mkdir(parents=True)
    (folder / "Show.S01E01.mkv").write_bytes(b"x")
    quarantine_path = tmp_path / "quarantine"

    new_path = quarantine(str(folder), str(quarantine_path), ["corrupted file"], attempts=1)
    assert new_path == str(quarantine_path / "Show S01")
    assert (quarantine_path / "Show S01" / "Show.S01E01.mkv").exists()
    reason = (quarantine_path / "Show S01.error.txt").read_text()
    assert "- corrupted file" in reason and "Attempts: 1" in reason

    # The same name again: both are kept
    folder.mkdir()
    second = quarantine(str(folder), str(quarantine_path), ["again"], attempts=6)
    assert second != new_path and (quarantine_path / "Show S01").exists()


@pytest.mark.parametrize("exitcode, failures, status", [
    (0, [], "done"),
    (None, [], "done"),
    (0, ["'Movie': upload refused by the tracker"], "failed"),
    (TEMPORARY_FAILURE, [], "retry"),
    (1, [], "failed"),
    (-9, [], "failed"),
])
def test_run_outcome(exitcode, failures, status):
    outcome = run_outcome(exitcode, reason="", failures=failures, errors=["last error"])
    assert outcome.status == status


class FakeBot(Bot):
    """ A Bot whose run is replaced by a function """

    def __init__(self, action):
        super().__init__(path="", cli=argparse.Namespace(), trackers_name_list=["ITT"])
        self.action = action

    def run(self, include_paths=None) -> bool:
        return self.action(include_paths[0])


def raise_temporary(path):
    raise TemporaryFailure("TRACKER Connection error")


def refused_upload(path):
    report.torrent_created(path + ".torrent")
    report.failed("Movie", "upload refused by the tracker: name already exists")
    return True


def crash(path):
    raise ValueError("bad file")


@pytest.mark.parametrize("action, status, reason", [
    (lambda path: True, "done", ""),
    (raise_temporary, "retry", "TRACKER Connection error"),
    (refused_upload, "failed", "'Movie': upload refused by the tracker: name already exists"),
    (crash, "failed", "ValueError: bad file"),
])
def test_run_isolated_in_a_child_process(tmp_path, action, status, reason):
    outcome = FakeBot(action)._run_isolated(include_path=str(tmp_path / "Movie.mkv"), timeout=60)
    assert (outcome.status, outcome.reason) == (status, reason)


def test_the_torrents_never_uploaded_are_read_from_the_journal(tmp_path):
    journal = str(tmp_path / "pending.json")
    outcome = FakeBot(refused_upload)._run_isolated(include_path=str(tmp_path / "Movie.mkv"), timeout=60,
                                                    journal=journal)
    assert outcome.pending_torrents == [str(tmp_path / "Movie.mkv") + ".torrent"]
    # Cleared for the next entry
    assert report.read_journal(journal) == []


def hang(path):
    report.torrent_created(path + ".torrent")
    import time
    time.sleep(30)


def test_a_stuck_upload_is_retried_and_its_torrent_is_known(tmp_path):
    journal = str(tmp_path / "pending.json")
    outcome = FakeBot(hang)._run_isolated(include_path=str(tmp_path / "Movie.mkv"), timeout=1, journal=journal)
    assert outcome.status == "retry"
    assert outcome.pending_torrents == [str(tmp_path / "Movie.mkv") + ".torrent"]


def queue_with(tmp_path, name="Movie.mkv"):
    movie = tmp_path / "destination" / name
    movie.parent.mkdir(exist_ok=True)
    movie.write_bytes(b"x")
    queue = UploadQueue(tmp_path / "queue.json")
    queue.add(str(movie))
    return queue, movie


def process(tmp_path, queue, outcomes: list[RunOutcome], max_retries=2):
    bot = FakeBot(lambda path: True)
    runs = []

    def run_isolated(include_path, timeout, journal=None):
        runs.append(include_path)
        return outcomes.pop(0)

    bot._run_isolated = run_isolated
    bot._process_queue(queue, timeout=0, quarantine_path=str(tmp_path / "quarantine"), max_retries=max_retries)
    return runs


def test_a_done_upload_leaves_the_queue(tmp_path):
    queue, movie = queue_with(tmp_path)
    process(tmp_path, queue, [RunOutcome("done")])
    assert len(queue) == 0 and movie.exists()


def test_a_temporary_error_is_retried_then_quarantined(tmp_path):
    queue, movie = queue_with(tmp_path)
    entry = queue.entries[0]
    torrent = tmp_path / "Movie.mkv.torrent"
    torrent.write_bytes(b"d")
    assert process(tmp_path, queue, [RunOutcome("retry", "network error", [str(torrent)])]) == [str(movie)]
    assert entry.attempts == 1 and len(queue) == 1
    # Not due yet
    assert process(tmp_path, queue, []) == []
    # The torrent never uploaded is removed: the retry would skip it as an old upload
    assert not torrent.exists()

    entry.next_attempt = 0
    assert process(tmp_path, queue, [RunOutcome("retry", "network error")]) == [str(movie)]
    assert entry.attempts == 2

    # Out of retries: quarantined
    entry.next_attempt = 0
    process(tmp_path, queue, [RunOutcome("retry", "network error")])
    assert len(queue) == 0 and not movie.exists()
    reason = (tmp_path / "quarantine" / "Movie.mkv.error.txt").read_text()
    assert "still failing after 2 retries" in reason


def test_a_failure_is_quarantined_at_once(tmp_path):
    queue, movie = queue_with(tmp_path)
    torrent = tmp_path / "Movie.mkv.torrent"
    torrent.write_bytes(b"d")
    process(tmp_path, queue, [RunOutcome("failed", "'Movie': upload refused", pending_torrents=[str(torrent)])])
    assert len(queue) == 0
    assert (tmp_path / "quarantine" / "Movie.mkv").exists()
    assert "upload refused" in (tmp_path / "quarantine" / "Movie.mkv.error.txt").read_text()
    # The torrent never uploaded is removed from the archive, or the watcher would skip it as an old upload
    assert not torrent.exists()


def test_the_watcher_resumes_the_queue_at_start(tmp_path):
    queue, movie = queue_with(tmp_path)
    bot = FakeBot(lambda path: True)
    resumed = []
    bot._run_isolated = lambda include_path, timeout, journal=None: resumed.append(include_path) or RunOutcome("done")
    # The watcher stopped during an upload: the torrent of that upload was never uploaded
    left = tmp_path / "Left.torrent"
    left.write_bytes(b"d")
    (tmp_path / "queue.pending.json").write_text(json.dumps([str(left)]))
    # The watcher folder doesn't exist: the watcher stops after resuming the queue
    assert bot.watcher(duration=1, watcher_path=str(tmp_path / "missing"), destination_path=str(movie.parent),
                       queue_file=str(tmp_path / "queue.json")) is False
    assert resumed == [str(movie)]
    assert json.loads((tmp_path / "queue.json").read_text()) == []
    assert not left.exists()


def test_an_entry_without_media_is_discarded(tmp_path):
    # Issue #75: a discarded entry must reach the quarantine, not stay in the destination folder
    (tmp_path / "notes.txt").write_text("not a video")
    bot = Bot(path=str(tmp_path), cli=argparse.Namespace(), mode="auto", trackers_name_list=["ITT"])
    report.reset()
    assert bot.run(include_paths=[str(tmp_path / "notes.txt")]) is False
    assert report.failures == ["'notes.txt': no media to upload: no video file or an unsupported type"]
    assert run_outcome(0, reason="", failures=report.failures, errors=[]).status == "failed"
    report.reset()


def test_a_content_in_another_language_is_discarded(monkeypatch):
    from ittup.core import config_settings
    from ittup.core.media_manager.common import UserContent

    monkeypatch.setattr(config_settings.user_preferences, "PREFERRED_LANG", "IT")
    content = argparse.Namespace(audio_languages=["en"], file_name="Movie.mkv", display_name="Movie")
    report.reset()
    assert UserContent.is_preferred_language(content) is False
    assert len(report.failures) == 1 and report.failures[0].startswith("'Movie': audio languages")
    report.reset()


def test_the_quarantine_path_of_the_config(tmp_path):
    from ittup.common.settings import Validate

    missing = tmp_path / "discarded"
    # Created when the first entry is quarantined: the folder doesn't need to exist yet
    assert Validate.unit3dup_path(str(missing), "WATCHER_QUARANTINE_PATH", "default", must_exist=False) == str(missing)
    assert Validate.unit3dup_path(str(missing), "WATCHER_PATH", "default") == "default"
    # '~' is expanded: the watcher would otherwise create a '~' folder in the working directory
    assert Validate.unit3dup_path("~/discarded", "WATCHER_QUARANTINE_PATH", "default",
                                  must_exist=False) == os.path.expanduser("~/discarded")
    assert Validate.unit3dup_path("", "WATCHER_QUARANTINE_PATH", "default", must_exist=False) == "default"
