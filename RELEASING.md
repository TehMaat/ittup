# Releasing ITTup

Work is merged into **dev**. At the feature freeze of a milestone, an **rc branch** `X.Y.Z-rcN` is cut from dev
and tested by real users; when it is OK it is merged into **main**, where release-please makes the release.
When it isn't, the fixes go to dev and a new rc is cut from dev. Only urgent **hotfixes** go to main directly.

```
 feat/… fix/… ai/… ──PR──▶ dev ●──●──●──┬──────●──●──┬───────────────●──▶   X.Y.Z.devN (dev channel)
                                        │   fix ▲    │               ▲
                              freeze    ▼       │    ▼               │ back-merge (PR, merge commit)
                               1.13.0-rc1 ──✗───┘  1.13.0-rc2 ──✓──┐ │
                               tag 1.13.0rc1       tag 1.13.0rc2   │ │  X.Y.ZrcN on PyPI (rc channel)
                                                                   ▼ │
 main ●──────────────────●─────────────────────────────────────────●─●──▶   X.Y.Z on PyPI (stable)
      1.12.1             ▲ 1.12.2 ──▶ back-merge to dev        merge commit → release-please → 1.13.0
                         │
          hotfix/1.12.2 ─┘ (from main, urgent only)
```

| Channel | Stability | Audience | Comes from | Published to | Install |
|---|---|---|---|---|---|
| **dev** | Low | Team | every commit on `dev` | workflow artifact; TestPyPI when enabled | `pip install --upgrade "git+https://github.com/TehMaat/ittup@dev"` or, from TestPyPI, `pip install --upgrade --pre -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ ittup` |
| **rc** | Medium-high | Testers | branch `X.Y.Z-rcN` | PyPI, as a pre-release | `pip install --upgrade --pre ittup` or `pip install ittup==X.Y.ZrcN` |
| **stable** | High | Everybody | `main`, release-please | PyPI | `pip install --upgrade ittup` |

pip ignores pre-releases (`.dev`, `rc`) without `--pre`, and the update check of ITTup only compares final
releases, so normal users never get a pre-release by mistake.

## Versions (PEP 440)

`MAJOR` for breaking changes (command line, config or data format), `MINOR` for compatible features,
`PATCH` for compatible fixes. **One milestone = one new version** (`X.Y.0`); patch versions are hotfixes.

| Channel | Format | Example |
|---|---|---|
| dev | `X.Y.Z.devN` | `1.12.2.dev812` |
| rc | branch `X.Y.Z-rcN`, version and tag `X.Y.ZrcN` | `1.13.0-rc2` → `1.13.0rc2` |
| stable | `X.Y.Z` | `1.13.0` |
| hotfix | `X.Y.Z+1` | `1.13.1` |

**Where the version comes from.** release-please is the only one that writes the version, in
`pyproject.toml`, `.release-please-manifest.json` and `CHANGELOG.md`, in its release PR on main: never edit them
by hand (CLAUDE.md). Tags have no `v` prefix (`1.13.0`, like every release so far). The dev and rc versions are
written into `pyproject.toml` only inside the CI workspace, at build time (`.github/scripts/set-version.sh`),
and never committed. That is why the project doesn't use `hatch-vcs`/`setuptools-scm`.

**Why merge commits.** release-please reads the commit subjects on main. Work is committed on dev, so the rc
branch must reach main with a **merge commit** (never squash): the `feat:`/`fix:` commits of dev arrive on main
and release-please computes the version and the changelog from them, as before. The back-merge main → dev is a
merge commit too, so dev always contains main.

## dev

Every work PR targets `dev` (the default branch). [`dev.yml`](.github/workflows/dev.yml), after `Tests` passes
on a push to dev:

1. Version: the patch after the latest release, plus the number of commits (`1.12.1` → `1.12.2.dev812`): it
   sorts after the latest release and before any next one.
2. Build, `twine check`, smoke and end-to-end tests **on the installed wheel** in a clean virtualenv.
3. The wheel and the sdist are kept as the workflow artifact `dist-dev`.
4. Published to TestPyPI only when the repository variable `TESTPYPI_PUBLISH` is `true`
   (TestPyPI trusted publisher: workflow `dev.yml`, environment `dev`).

Unfinished features on dev stay behind an option of the config (as the existing `*_SCSHOT` options), off by
default.

## rc

At the feature freeze of milestone `1.13.0`:

1. On dev only fixes, tests and docs get merged from now on, until the release.
2. Cut the rc branch from dev:

   ```bash
   git fetch origin && git push origin origin/dev:refs/heads/1.13.0-rc1
   ```

3. [`rc.yml`](.github/workflows/rc.yml) checks:
   - the name (`X.Y.Z-rcN`), that the branch is a commit of dev, that `X.Y.Z` isn't released and `X.Y.ZrcN`
     doesn't exist;
   - the **milestone** `X.Y.Z` exists and has no open P0/P1 issue and no open `sev:blocker`/`sev:critical` bug.

   Then it runs the full test matrix (`pip-audit` blocking) and the Windows unit tests, builds `1.13.0rc1`,
   tests the wheel, **tags `1.13.0rc1`**, publishes it on PyPI as a pre-release (environment `staging`),
   installs it back from PyPI and prints the install command for the testers in the run summary.
4. **Soak period**: at least 3-5 days of real use, following [docs/release-testing.md](docs/release-testing.md).
5. **KO**: the rc branch is not fixed and not merged. The fix is a PR to dev; then cut the next rc from dev,
   `1.13.0-rc2`, and the soak starts over.
6. **OK**: go to the release.

An rc branch is never changed after it is cut (ruleset). PyPI needs a trusted publisher for workflow `rc.yml`
and environment `staging` (once, see "PyPI and TestPyPI" below).

## stable

1. Open the PR **`1.13.0-rc2` → main** and merge it with a **merge commit** (both developers agree: one
   approves the PR, the other approves the deployment).
2. release-please updates its release PR on main with version `1.13.0` and the changelog: review it, merge it.
3. [`publish.yml`](.github/workflows/publish.yml): release-please creates the tag `1.13.0` and the GitHub release;
   the build checks the tag matches `pyproject.toml` and that the release is **the code of its last rc**
   (only the version and the changelog may differ: otherwise a warning, an error with the repository variable
   `STRICT_RELEASE=true`); `pip-audit` warns.
4. The `pypi` environment waits for the **manual approval** of a maintainer, then publishes to PyPI with trusted
   publishing. Its name is the one in the PyPI trusted publisher: don't rename it.
5. Smoke test: `pip install ittup==1.13.0` from PyPI in a clean virtualenv, then `ittup --help`.
6. The milestone `1.13.0` is closed; its open issues move to the next milestone or back to the backlog.
7. A PR **main → dev** ("chore: back-merge main into dev", from the copy `back-merge/main`) is opened
   automatically: merge it with a merge commit.

## Hotfix

Only for fixes that must reach users at once and can't wait for the next milestone:

1. `git switch -c hotfix/1.13.1 origin/main`, the fix plus a regression test, commit `fix: …`.
2. PR `hotfix/1.13.1` → main (CI accepts only rc and hotfix branches on main), merge commit.
3. release-please proposes `1.13.1`: merge the release PR, approve the `pypi` deployment. A patch release
   without an rc is fine for the release check (a notice).
4. Merge the automatic back-merge PR main → dev, so the fix is also in the next rc.

## Rollback

- **PyPI**: *yank* the broken version (it stays installable only when asked for explicitly) and publish a hotfix
  at once, or tell the users the previous version: `pip install ittup==X.Y.Z`.
- Note the rollback in the release notes and open a P0 issue with a regression test.
- Within the same `MAJOR`, the config and the data stay backwards compatible, so going back to the previous
  version always works.
- A published version is never overwritten (PyPI doesn't allow it anyway): a mistake is fixed with a new version.

## CI environments

| Environment | Channel | Protection |
|---|---|---|
| `dev` | dev | None, automatic |
| `staging` | rc | Only rc branches `*-rc*` |
| `pypi` (production) | stable | Only branch `main`, plus a required reviewer |
| `github-pages` | docs | As before (`docs.yml`, from main) |

## PyPI and TestPyPI

Publishing uses **trusted publishing** (OIDC): no token is stored in GitHub. PyPI trusts a specific workflow file
of a specific repository, optionally limited to a GitHub environment. A project can have several trusted
publishers: one per workflow below.

### PyPI (rc and stable): https://pypi.org/manage/project/ittup/settings/publishing/

Only an owner of the `ittup` project can do this (today TehMaat). Section "Add a new publisher" → GitHub:

| Field | Stable (exists already) | rc (to add) |
|---|---|---|
| Owner | `TehMaat` | `TehMaat` |
| Repository name | `ittup` | `ittup` |
| Workflow name | `publish.yml` | `rc.yml` |
| Environment name | `pypi` | `staging` |

- The owner is the repository the release runs from: only `TehMaat/ittup`. Never add a fork as a publisher
  of the real project: the fork could then publish versions of `ittup` to every user. On a fork (e.g. the one
  used to present these changes) the PyPI step of `publish` and `rc` fails (no trusted publisher); everything
  before it (tests, build, wheel checks, tags) works.
- An rc published on PyPI can't be deleted and re-uploaded with the same number: a broken rc is *yanked* and the
  next rc gets the next number.
- Recommended in the project settings: two-factor authentication for every owner and maintainer; the second
  developer as **Maintainer** (can upload, can't delete the project), not Owner.
- Optional: project → Settings → "Notifications" on, to be emailed at every new release.

### TestPyPI (dev): https://test.pypi.org/manage/account/publishing/

The name `ittup` isn't registered on TestPyPI yet, so the publisher is a **pending publisher**: it creates the
project at the first upload. With a TestPyPI account (separate from PyPI, with 2FA), "Add a new pending
publisher" → GitHub:

| Field | Value |
|---|---|
| PyPI Project Name | `ittup` |
| Owner | `TehMaat` |
| Repository name | `ittup` |
| Workflow name | `dev.yml` |
| Environment name | `dev` |

Then turn the upload on: `gh variable set TESTPYPI_PUBLISH -b true -R TehMaat/ittup`.
TestPyPI is a test index: it may be wiped, and its other packages are not trusted. That's why the install
command takes the dependencies from PyPI (`--extra-index-url https://pypi.org/simple/`).

### Check

- rc: cut an rc branch; the `publish` job of `rc.yml` shows "Publishing distribution to PyPI" and
  https://pypi.org/project/ittup/#history lists the version marked "pre-release".
- dev: after a push to dev, https://test.pypi.org/project/ittup/#history lists `X.Y.Z.devN`.
- An error `invalid-publisher` means one of the four fields doesn't match: the workflow file name, the
  environment name and the repository owner are case sensitive.

## Setup (once per repository)

To do on `TehMaat/ittup` (a fork can be set up the same way to try the flow, without the PyPI part):

- Create `dev` from main and make it the default branch.
- Settings → Environments: `dev`, `staging`, `pypi` with the protections above; on `pypi` add both maintainers as
  required reviewers.
- PyPI and TestPyPI trusted publishers: see "PyPI and TestPyPI" above.
- Rulesets: `dev` (PR required, no force push, no deletion); `main` (the same, merge commits only); rc branches
  `*-rc*` (no update, no force push: they can be created but not changed); tags (no update, no deletion, except
  `archive/*`). Maintainers (admin) can bypass them. Plus one ruleset **without any bypass** that forbids deleting
  `main` and `dev`: "Automatically delete head branches" acts as the person who merges, so an admin bypass let
  it delete `main` once (the head of a back-merge PR).
- Settings → Actions → General: "Allow GitHub Actions to create and approve pull requests" (release-please and
  the back-merge PR need it); "Require approval for all external contributors".
- Settings → General: "Automatically delete head branches", Issues and Discussions on.
- Run the `Labels` workflow once.

## Checklists

The Milestone issue form holds the full checklists. In short:

**Feature freeze → rc**: P0/P1 done or explicitly postponed · no AI PR pending for this milestone · branch
`X.Y.0-rc1` cut from dev · `rc.yml` green (milestone, tests, matrix, tag, smoke from PyPI) · testers told.

**rc → stable**: soak passed · no open blocking/critical bug · `pip-audit` clean · PR rc → main merged with a
merge commit · release PR reviewed and merged · `pypi` deployment approved · smoke green · back-merge merged.
