# Contributing to ITTup

ITTup is developed by a small team (2+ developers), with a large share of the code written with AI
assistants and agents. This file is the process: planning, priorities, issues, branches, pull requests,
tests and the rules for AI. Releases and distribution channels are in [RELEASING.md](RELEASING.md).

## Local setup

```bash
git clone https://github.com/TehMaat/ittup.git && cd ittup   # the default branch is dev
python -m venv .venv && . .venv/bin/activate
pip install -e . pytest pytest-cov pre-commit
pre-commit install --hook-type pre-commit --hook-type pre-push
```

The end-to-end tests need `ffmpeg` and `ffprobe` (5.1+) on the PATH.

| Command | What it runs |
|---|---|
| `pytest -q --ignore=tests/e2e` | Unit tests (seconds) |
| `pytest -q --ignore=tests/e2e --cov` | Unit tests with coverage, fails under `fail_under` in `pyproject.toml` |
| `pytest -v tests/e2e` | The `ittup` command on dummy files, with a fake tracker, TMDB, TVDB and image hosts |
| `pytest -v tests/smoke` | The installed `ittup` starts |
| `ruff check .` | Lint (CI compares the count with `.github/quality-baseline.conf`) |
| `mypy` | Types of `ittup/common/` (same baseline) |
| `bandit -c pyproject.toml -r ittup -lll` | High severity security issues |
| `pip-audit -r requirements.txt` | Known vulnerabilities in the dependencies |

## Roles

| Role | Responsibility |
|---|---|
| **Milestone owner** | Scope, priorities, promotion of the channels. Rotates every milestone |
| **Reviewer** | Reviews every PR, AI ones included. Never the person who opened or guided the PR |
| **Release manager** | rc tags, release PR, changelog check. The milestone owner |

With two developers: the milestone owner is the release manager, the other one is the reference reviewer,
and **every promotion (dev → rc → release) needs the ok of both**.

## Milestones

**One milestone = one new version.** Every version except a hotfix is the result of a milestone, and every rc
belongs to the milestone of its version. A milestone is created **at the start** of its development cycle, not
just before the rc, with: a goal (1-2 sentences), feature freeze and release dates, an owner and the exit criteria
below. Recommended length: 2-4 weeks.

On GitHub (Issues → Milestones):

1. Create the milestone named exactly as the version, `X.Y.0` (no `v`), with the release date as due date and in
   the description the goal, the freeze date and the owner.
2. Open its tracking issue with the **Milestone** form and assign it to the milestone: it holds the checklists.
3. At triage, assign the issues to the milestone. Name milestones `X.Y.0`: release-please picks the version from
   the commits, and any `feat:` makes the next version a minor one.
4. `rc.yml` refuses to cut an rc when the milestone doesn't exist or still has open P0/P1 issues or
   blocking/critical bugs.
5. At the release, `publish.yml` closes the milestone and moves its open issues to the next milestone (by due
   date) or back to the backlog, with a comment.

Hotfixes don't wait for a milestone. To track one, open a small milestone `X.Y.Z` and close it with the hotfix.

```
Planned → In development → Feature freeze → Release candidate → Released → Closed
```

| State | Channel | What gets in |
|---|---|---|
| Planned | – | Triage and priorities |
| In development | dev | Features, fixes, refactoring |
| Feature freeze | dev → rc | Branch `X.Y.0-rc1` cut from dev; on dev only fixes, tests, docs |
| Release candidate | rc | Only blocking/critical fixes, on dev, then a new rc from dev |
| Released | release | Nothing: fixes go to a patch |
| Closed | – | Retrospective done |

**Exit criteria**: all P0 and P1 items closed · no open blocking or critical bug · CI green on every
supported Python · coverage not lower than the previous release · docs updated (the changelog is
release-please's) · at least one rc survived the soak period.

**Scope rules**: plan at most 80% of the estimated capacity; estimate **review and verification time**, not
just writing time (with AI writing is cheap, review isn't); no new features after the freeze, they move
to the next milestone; unfinished items are re-planned explicitly.

## Priorities

| Priority | Meaning | Effect |
|---|---|---|
| **P0 – Critical** | The release doesn't ship without it | Blocks the release, absolute precedence |
| **P1 – High** | Main goal of the milestone | Must be done; escalate at once if at risk |
| **P2 – Medium** | Important but can wait | Done if there is capacity |
| **P3 – Low** | Nice to have | First to be postponed; good for AI agents and newcomers |

Bug severity (`sev:*` labels) and indicative priority: *blocker* (crash at start, data loss, vulnerability)
→ P0 · *critical* (main feature unusable, no workaround) → P0/P1 · *major* (degraded, workaround) → P1/P2 ·
*minor* (cosmetic) → P2/P3.

To assign a priority, score each item 1-3 on **impact** (users/use cases), **urgency** (deadlines, growing
risk) and **effort, inverted** (low effort, review included = 3): `score = impact × urgency + effort`.
≥ 10 → P1 (P0 if blocking) · 6-9 → P2 · ≤ 5 → P3. The owner may override it, explaining why in the issue.

Capacity of a milestone: P0 20% reserved margin · P1 ~50-60% · P2 ~20-30% · P3 ~10%.

## Triage

Weekly, 15-30 minutes, both developers. For every `needs-triage` issue:

1. **Duplicate?** → close as `duplicate` with a link to the original.
2. **Out of scope?** → close as `not-planned`, with the reason.
3. **Missing data?** → `needs-info` with a precise question.
4. **Valid** → type, priority, severity (bugs), milestone or backlog, mode (`ai-agent`, `ai-assisted`,
   `manual`) → `ready` if it meets the Definition of Ready, otherwise it stays in triage with an owner.

First answer within **5 working days**; a bug reported as blocking within **1 working day**. A new P0 in a
running milestone pushes out a P2/P3 of similar effort. An item postponed twice is re-evaluated or closed.

## Issues

- **Every piece of work starts from an issue**: no PR without one, except typos and trivial fixes.
- **One issue = one checkable result.** If it needs several PRs or days, it becomes an `epic` with sub-issues.
- Issues are opened **only with the forms** (bug, feature, task, docs). Questions go to Discussions,
  vulnerabilities to a private advisory ([SECURITY.md](SECURITY.md)).
- Priority, severity and milestone are set by the team, never by the reporter.

### Lifecycle

```
needs-triage ──▶ needs-info ──▶ (answer) ──▶ needs-triage
      ├──▶ ready ──▶ in-progress ──▶ review ──▶ closed (by the merge)
      │                  └── blocked
      └──▶ closed: duplicate · wontfix · not-planned · invalid
```

### Definition of Ready

An issue becomes `ready` only with: type, priority and (bugs) severity · milestone or backlog · checkable
acceptance criteria · mode · size S or M (L is split) · for bugs: reproduced by the team.
For `ai-agent` issues it is **binding**: an agent works only on `ready` issues.

### Linking

- The branch has the issue number: `feat/123-export-csv`.
- The PR description has `Closes #123` (CI warns without it): the issue closes when the PR is merged into dev,
  the default branch. A hotfix PR to main closes its issue too only after the back-merge; close it by hand.
- One assignee per issue; when an AI agent works on it, the assignee is the person guiding it.

### Maintenance (automated by `stale.yml`)

| Situation | Action |
|---|---|
| `needs-info` without answer for 14 days | `stale`, closed after 14 more |
| PR without activity for 30 days | `stale`, closed after 14 more |
| Backlog without activity for 6 months | Re-evaluated at milestone close: re-planned or `not-planned` |
| `in-progress` without commits for 14 days | The assignee updates it or puts it back to `ready` |
| A closed bug comes back | New issue linking the old one (don't reopen one already released) |

P0, P1, `epic` and `keep` are never marked stale. Closed issues are never deleted.

### Labels

Defined in [.github/labels.yml](.github/labels.yml) and synced by a workflow: priority `P0`-`P3`; type
`feature`, `bug`, `chore`, `docs`, `security`, `epic`; severity `sev:*`; `found-in:dev|rc|release`; mode
`ai-agent`, `ai-assisted`, `manual` (and `ai-generated` on PRs); status `needs-triage`, `needs-info`, `ready`,
`in-progress`, `blocked`, `review`; closing `duplicate`, `not-planned`, `invalid`, `wontfix`; `external`,
`good first issue`, `help wanted`; `stale`; `keep` (excluded from pruning and stale).

### Project board

One GitHub Project for the repository with the fields Status (Triage, Ready, In progress, Blocked, Review,
Done), Priority (P0-P3), Milestone, Mode, Size (S, M, L), and the views: current milestone by status, triage,
backlog by priority, AI (`ai-agent` + ready). Turn on the Project's built-in workflows "Auto-add to project"
(new issues → Triage), "Pull request linked → Review" and "Item closed → Done". The board fields are the source
of truth for status and priority; the `P*` labels stay for filters and automations.

## Branches

| Prefix | Use | Example |
|---|---|---|
| `dev` | Development, dev channel, **default branch**: every work PR targets it | – |
| `X.Y.Z-rcN` | Release candidate cut from dev, never changed, merged into main when OK | `1.13.0-rc2` |
| `main` | Released code only: receives rc branches, hotfixes and release-please's release PR | – |
| `hotfix/X.Y.Z` | Urgent fix, from main to main (RELEASING.md) | `hotfix/1.12.2` |
| `feat/<issue>-<descr>` | Feature | `feat/123-export-csv` |
| `fix/<issue>-<descr>` | Bug fix | `fix/140-crash-config` |
| `chore/`, `docs/`, `ci/`, `test/` | Maintenance, docs | `chore/bump-ruff` |
| `ai/<issue>-<descr>` | Branches created by AI agents (`claude/*` too) | `ai/151-add-tests` |

- Head branches are **deleted automatically at merge**.
- `dev` and `main` are protected (no direct push, no force push, no deletion; main only with merge commits); rc
  branches can't be changed after they are cut; tags can't be updated or deleted (except `archive/*`).
- Merging into dev: squash (the PR title is the commit) or merge commit. Merging into main and the back-merge
  main → dev: **always a merge commit**, never squash, so release-please finds every commit of dev on main.
- **Obsolete branches** (`prune-branches.yml`, every Monday): a branch is deleted only when it is **merged
  into dev or main and has had no commits for more than 3 months** (90 days). Branches that aren't merged are never
  deleted automatically: the ones inactive for more than 3 months are listed in the report, to be checked by
  hand. Branches with an open PR (also one to the original repository, for a fork) or a PR labeled `keep` are
  never touched. The schedule only reports; deleting is a manual run with `dry_run` unchecked.
- Local cleanup, from time to time:

  ```bash
  git config --global fetch.prune true
  git fetch --prune --prune-tags
  git branch --merged origin/dev | grep -vE '^\*|main|dev' | xargs -r git branch -d
  git branch -vv | grep ': gone]'   # local branches whose remote no longer exists
  ```

## Pull requests

- The **title** is a [Conventional Commit](https://www.conventionalcommits.org/), and so is **every commit**:
  release-please reads them to pick the next version and write the changelog (see [CLAUDE.md](CLAUDE.md)).
  CI checks both.
- Every commit is signed off (`git commit -s`, [DCO](https://developercertificate.org/)): you certify you
  have the right to submit it under the project's license. CI checks it (bots excepted).
- **Small PRs**: under ~400 changed lines; split bigger ones.
- Human review is mandatory; nobody merges their own PR without review, and **an AI agent never merges**.
- Quality gates, required on every PR: tests on the oldest and newest Python, coverage not under
  `fail_under`, ruff and mypy not above the baseline, bandit with no high severity issue, build and
  `twine check`. `pip-audit` warns on PRs and blocks on rc.

## Tests

| Level | What | Where |
|---|---|---|
| **Unit** | Functions and classes, no real I/O | `tests/test_*.py` |
| **End-to-end** | The `ittup` command on dummy videos, fake network | `tests/e2e/` |
| **Smoke** | The installed package starts | `tests/smoke/` |

| Event | Unit | E2E | Smoke on the wheel | Python matrix |
|---|---|---|---|---|
| pre-commit / pre-push | ✓ (pre-push) | – | – | – |
| PR | ✓ | ✓ | – | 3.11, 3.14 |
| Push on dev (dev channel) | ✓ | ✓ (also on the wheel) | ✓ | 3.11-3.14 |
| Push on main | ✓ | ✓ | – | 3.11-3.14 |
| rc branch | ✓ | ✓ (also on the wheel) | ✓ (also from PyPI) | 3.11-3.14 + Windows unit tests |
| Release | – (code of the rc) | – | ✓ after publishing | – |
| Nightly on dev | ✓ | ✓ | – | 3.11-3.14, latest dependencies |

Rules:

- **Every fixed bug has a regression test** that fails before the fix.
- Coverage: never lower than `fail_under` (raise it when dev goes up); new code should be covered better
  than the rest.
- **Flaky** tests are marked `@pytest.mark.flaky`, get a P2 issue and are fixed within the milestone.
- No calls to real services in tests: mocks, fixtures or `tests/e2e/fake_network.py`.
- Fixtures contain no real data or credentials.

## AI

**AI writes code, people are responsible for it.** Whoever opens or guides an AI PR answers for it as if
they had written it by hand.

| Kind of item | Mode |
|---|---|
| Tests, docstrings, mechanical refactoring, well specified P3 | `ai-agent` (autonomous agent, then review) |
| P1/P2 features with a clear specification | `ai-assisted` (a developer guides, the AI writes) |
| Security, data handling, migrations (config upgrade), architecture, P0 | `manual` or `ai-assisted` with a reinforced review |

- An item goes to AI only with an **issue with written acceptance criteria** (input, expected output, edge
  cases); without them it goes back to triage.
- Label the PR `ai-generated` or `ai-assisted` and tick the AI box in the template.
- Read the tests the AI writes: they must check the **expected behavior**, not mirror the implementation;
  no tests that always pass (empty asserts, mocks returning the expected result, `try/except` hiding errors);
  the edge cases of the acceptance criteria are covered. If the AI changes an existing test to make it pass,
  the PR explains why the expected behavior changed.
- Check every **new dependency**: it exists, is maintained and is the right package (risk of non-existent or
  look-alike packages).
- No secrets, tracker URLs, passkeys or credentials in prompts or in generated code.
- The AI context file is [CLAUDE.md](CLAUDE.md): conventions, test commands, things not to do.
- At most 2-3 open AI PRs per reviewer; AI PRs not reviewed by the feature freeze move to the next milestone.
- For critical modules, consider mutation testing (`mutmut`) at every rc.

## External contributions

```
Issue (feature) ──▶ discussion + ok of the team ──▶ fork ──▶ PR to dev
   ──▶ labels external + needs-triage ──▶ triage ──▶ CI approved ──▶ review ──▶ merge
                                       └──▶ or closed with a reason / stale
```

- **Features**: an issue agreed with the team first, then the PR. A feature PR without an agreed issue may be
  closed politely. **Fixes, docs, typos**: a direct PR is fine.
- External PRs always target `dev`, never `main`, an rc branch or `hotfix/*`: the team decides what goes into
  an rc or a hotfix.
- First answer within 5 working days, first full review within 10. No answer from the contributor: `stale`
  after 30 days, closed after 14 more.
- At triage the PR gets a priority, a milestone (decided by the team) and a team member who follows it.
  External PRs respect the feature freeze.
- **CI security**: workflows from forks run only after a maintainer approves them; they use `pull_request`,
  never `pull_request_target` with the PR's code, so forks never see secrets; external PRs publish nothing.
  Before approving the CI, check changes to `.github/workflows/`, `pyproject.toml`, `requirements.txt`,
  `tests/conftest.py` and `.pre-commit-config.yaml` ([CODEOWNERS](.github/CODEOWNERS) requires the team's review).
- **AI in external PRs**: declare it in the template; you must have run and understood the code and be able
  to answer questions on it. PRs are closed without a deep review when they have no agreed issue (features),
  fail the basic checks, or are evidently mass-generated, generic or unrelated. New dependencies from
  external PRs are checked with extra suspicion.
- Review by at least one maintainer; changes to critical modules, dependencies or packaging need **both**.
  Maintainers may push small fixes to the contributor's branch ("Allow edits by maintainers").
- Merge keeping the contributor's authorship (`Co-authored-by` on a squash). The contribution appears in the
  changelog and release notes.
- Every PR closed without merge has a written reason (out of scope, duplicate, different approach planned,
  inactivity). If the idea is good but the implementation isn't, open or link an issue to keep it.
- `good first issue` and `help wanted` go on well specified P3 items; those are not given to an AI agent of the
  team at the same time.

## Checklists

**Triage of a new issue**: not a duplicate nor out of scope · type, priority, severity · milestone or backlog ·
acceptance criteria and mode · size S/M (or split) · `ready` or `needs-info`.

**External PR**: DCO · linked issue (features) · sensitive files checked before approving the CI · priority,
milestone, owner · quality gates green · review done, authorship kept · contribution in the changelog.

**Milestone opening**: target version, goal, freeze and release dates · items triaged with priority and mode ·
acceptance criteria for AI items · capacity ≤ 80%, review included.

**Milestone closing**: release published and installation checked · leftover items re-planned · retrospective
(what slipped, how much AI code needed rework and why) · branch report reviewed, merged `hotfix/*` deleted · backlog idle for 6 months re-evaluated.
