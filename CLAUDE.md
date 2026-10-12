# ittup

## Commit messages

Releases are automated with release-please, which reads the commit history on `main`
to pick the next version and write `CHANGELOG.md`. Write every commit subject as a
[Conventional Commit](https://www.conventionalcommits.org/):

- `fix: ...` for bug fixes (patch release)
- `feat: ...` for new features (minor release)
- `feat!: ...` or a `BREAKING CHANGE:` footer for incompatible changes (major release)
- `docs:`, `ci:`, `refactor:`, `chore:`, `test:` for changes that don't need a release

Don't edit `version` in `pyproject.toml` or `CHANGELOG.md` by hand: release-please does it
in its release PR.
