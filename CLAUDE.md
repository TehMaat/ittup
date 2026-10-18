# ittup

## Commit messages

Releases are automated with release-please, which reads the commit history on `main`
to pick the next version and write `CHANGELOG.md`. Commits are made on `dev` and reach `main`
through an rc branch merged with a merge commit, so their subjects are what release-please reads. Write every commit subject as a
[Conventional Commit](https://www.conventionalcommits.org/):

- `fix: ...` for bug fixes (patch release)
- `feat: ...` for new features (minor release)
- `feat!: ...` or a `BREAKING CHANGE:` footer for incompatible changes (major release)
- `docs:`, `ci:`, `refactor:`, `chore:`, `test:` for changes that don't need a release

Don't edit `version` in `pyproject.toml` or `CHANGELOG.md` by hand: release-please does it
in its release PR.

## Process

The development and release process is in `CONTRIBUTING.md` (issues, priorities, branches, PRs, tests, AI rules)
and `RELEASING.md` (dev, rc and release channels). The parts that matter most when you write code:

- Work only from an issue with acceptance criteria; the branch is `ai/<issue>-<descr>` (or the type prefix,
  e.g. `fix/140-crash-config`), created from `dev`, and the PR targets `dev`, never `main`. The PR description
  has `Closes #<issue>`.
- Never commit to an rc branch (`X.Y.Z-rcN`) or open a PR to `main`: rc branches are cut from `dev` by the
  maintainers, and only they open the rc → main and hotfix PRs.
- Every commit subject is a Conventional Commit (above) and is signed off: `git commit -s` (CI checks both).
- Keep PRs under ~400 changed lines. Never merge a PR: a person reviews and merges it.
- Every new function comes with tests; every fixed bug with a regression test that fails before the fix.
  Don't change an existing test just to make it pass: if the expected behavior changed, say why in the PR.
- Add a dependency only after checking it exists on PyPI, is maintained and is the right package.
- No secrets, API keys, passkeys or tracker URLs in code, tests or fixtures.

## Commands

```bash
pip install -e . pytest pytest-cov
pytest -q --ignore=tests/e2e --cov   # unit tests, coverage must stay >= fail_under in pyproject.toml
pytest -v tests/e2e                  # end-to-end, needs ffmpeg/ffprobe 5.1+
ruff check .                         # must not exceed RUFF_MAX in .github/quality-baseline.conf
mypy                                 # must not exceed MYPY_MAX
bandit -c pyproject.toml -r ittup -lll
```

## Don't

- Don't write a dev or rc version anywhere: CI builds them from the dev branch and the rc branches (`RELEASING.md`).
- Don't raise the numbers in `.github/quality-baseline.conf` or lower `fail_under`: fix the new errors instead.
- Don't rename the `pypi` environment in `publish.yml`: the PyPI trusted publisher depends on it.
- Don't use `pull_request_target` in workflows.
