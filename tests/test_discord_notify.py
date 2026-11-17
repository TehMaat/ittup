"""The Discord announcement of rc and stable releases (.github/scripts/discord-notify.sh)."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "discord-notify.sh"

pytestmark = pytest.mark.skipif(
    sys.platform == "win32" or not (shutil.which("bash") and shutil.which("jq") and shutil.which("git")),
    reason="the release workflows run the script on Linux with bash, jq and git",
)

STABLE_NOTES = """## [1.13.0](https://github.com/TehMaat/ittup/compare/1.12.2...1.13.0) (2026-11-20)


### ⚠ BREAKING CHANGES

* drop Python 3.9

### Features

* **upload:** force the resolution ([a1b2c3d](https://github.com/TehMaat/ittup/commit/a1b2c3d))

### Bug Fixes

* duplicate check counts symlinks ([d4e5f6a](https://github.com/TehMaat/ittup/commit/d4e5f6a))
"""


def run(args, cwd, **env):
    environ = {k: v for k, v in os.environ.items() if k not in ("DISCORD_WEBHOOK_URL", "NOTES", "GITHUB_REPOSITORY")}
    environ.update(env)
    return subprocess.run(
        ["bash", str(SCRIPT), *args], cwd=cwd, env=environ, capture_output=True, text=True, check=True
    )


def embed(args, cwd, **env):
    payload = json.loads(run(["--dry-run", *args], cwd, **env).stdout)
    assert payload["allowed_mentions"] == {"parse": []}
    return payload["embeds"][0]


GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"}


def git(cwd, *args):
    subprocess.run(["git", "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *args],
                   cwd=cwd, env={**os.environ, **GIT_ENV}, check=True, capture_output=True)


def commit(cwd, subject):
    git(cwd, "commit", "-q", "--allow-empty", "-m", subject)


@pytest.fixture
def repo(tmp_path):
    """A repository with the stable release 1.12.2."""
    git(tmp_path, "init", "-q")
    commit(tmp_path, "feat: released in 1.12.2")
    git(tmp_path, "tag", "1.12.2")
    return tmp_path


def test_rc_lists_the_commits_since_the_last_stable_tag(repo):
    commit(repo, "feat: force the resolution")
    commit(repo, "fix(upload): crash on an empty folder")
    commit(repo, "docs: not in the notes")
    commit(repo, "feat!: drop Python 3.9")
    git(repo, "tag", "1.13.0rc1")

    e = embed(["rc", "1.13.0rc1"], repo)

    assert e["title"] == "🧪 ITTup 1.13.0rc1 — versione di prova"
    assert e["url"] == "https://github.com/TehMaat/ittup/compare/1.12.2...1.13.0rc1"
    assert e["color"] == 15105570
    assert e["footer"]["text"] == "Provatela per 3-5 giorni e segnalate i problemi con una issue."
    d = e["description"]
    assert d.startswith("**⚠ Modifiche incompatibili**\n- drop Python 3.9\n\n**Novità**\n- force the resolution\n\n"
                        "**Correzioni**\n- **upload:** crash on an empty folder\n\n")
    assert "released in 1.12.2" not in d and "not in the notes" not in d
    assert '```\npip install --upgrade --pre "ittup==1.13.0rc1"\n```' in d
    assert "[PyPI](https://pypi.org/project/ittup/1.13.0rc1/)" in d


def test_rc_without_a_stable_tag_links_the_commits(tmp_path):
    git(tmp_path, "init", "-q")
    commit(tmp_path, "chore: first")

    e = embed(["rc", "0.1.0rc1"], tmp_path)

    assert e["url"] == "https://github.com/TehMaat/ittup/commits/0.1.0rc1"
    assert e["description"].startswith("Nessuna novità o correzione.\n")


def test_stable_translates_the_release_please_notes(tmp_path):
    url = "https://github.com/TehMaat/ittup/releases/tag/1.13.0"

    e = embed(["stable", "1.13.0", url], tmp_path, NOTES=STABLE_NOTES)

    assert e["title"] == "🚀 ITTup 1.13.0 è uscita"
    assert e["url"] == url
    assert e["color"] == 3066993
    assert "footer" not in e
    assert e["description"] == (
        "**⚠ Modifiche incompatibili**\n- drop Python 3.9\n\n"
        "**Novità**\n- **upload:** force the resolution ([a1b2c3d](https://github.com/TehMaat/ittup/commit/a1b2c3d))\n\n"
        "**Correzioni**\n- duplicate check counts symlinks ([d4e5f6a](https://github.com/TehMaat/ittup/commit/d4e5f6a))"
        "\n\n**Installa o aggiorna**\n```\npip install --upgrade ittup\n```\n"
        f"🔗 [Release su GitHub]({url}) · [PyPI](https://pypi.org/project/ittup/1.13.0/)"
    )


def test_long_notes_are_cut_at_a_line_with_a_link(tmp_path):
    url = "https://github.com/TehMaat/ittup/releases/tag/2.0.0"
    notes = "### Features\n\n" + "".join(f"* feature number {i} with a long enough description\n" for i in range(200))

    d = embed(["stable", "2.0.0", url], tmp_path, NOTES=notes)["description"]

    assert len(d) <= 4096
    assert f"… [note complete su GitHub]({url})" in d
    assert "- feature number 0 " in d and "feature number 199" not in d
    assert d.endswith("[PyPI](https://pypi.org/project/ittup/2.0.0/)")
    for line in d.split("\n"):
        assert not line.startswith("- ") or line.endswith("description")


def test_special_characters_and_mentions_stay_text(repo):
    subject = 'fix: "quotes" `backticks` \\ $HOME *bold* @everyone @here <@123>'
    commit(repo, subject)

    d = embed(["rc", "1.12.3rc1"], repo)["description"]

    assert f"- {subject[5:]}\n" in d


def test_without_the_webhook_nothing_is_sent(tmp_path):
    result = run(["stable", "1.13.0", "https://example.com"], tmp_path, NOTES=STABLE_NOTES)

    assert "::notice::DISCORD_WEBHOOK_URL is not set" in result.stdout


def test_a_failed_post_is_a_warning_and_hides_the_webhook(tmp_path):
    webhook = "http://127.0.0.1:9/api/webhooks/1/not-a-real-token"

    result = run(["stable", "1.13.0", "https://example.com"], tmp_path, NOTES=STABLE_NOTES,
                 DISCORD_WEBHOOK_URL=webhook)

    assert "::warning::The Discord announcement of 1.13.0 failed" in result.stdout
    assert "not-a-real-token" not in result.stdout + result.stderr


def test_an_unknown_kind_fails(tmp_path):
    with pytest.raises(subprocess.CalledProcessError):
        run(["--dry-run", "beta", "1.0.0"], tmp_path)
