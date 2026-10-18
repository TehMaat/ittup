<!-- Work PRs target dev. Only an rc branch (X.Y.Z-rcN) or a hotfix (hotfix/*) targets main (RELEASING.md).
     The title is a Conventional Commit: release-please uses it for the version and the changelog (CLAUDE.md).
     fix: ... (patch) · feat: ... (minor) · feat!: ... (breaking) · docs:/ci:/refactor:/chore:/test: (no release) -->

Closes #

## What changes and why

## How it was tested

## Checklist

- [ ] The linked issue was agreed with the team (required for features)
- [ ] Every new function has tests; every fixed bug has a regression test that fails without the fix
- [ ] An existing test was changed only because the expected behavior changed (explained above)
- [ ] New dependencies are checked: they exist, are maintained and are the right package
- [ ] No secrets, tokens, tracker URLs or real user data in the code, tests or fixtures
- [ ] Docs (`docs/docs/`, English and Italian) updated if the behavior changes
- [ ] Commits signed off (`git commit -s`, DCO)

## AI

- [ ] No AI was used
- [ ] AI-assisted: I guided the AI, I ran and understood all the code and can answer questions on it
- [ ] AI agent: an agent wrote it from the issue's acceptance criteria; I reviewed all of it
<!-- With AI, add the ai-assisted or ai-generated label -->
