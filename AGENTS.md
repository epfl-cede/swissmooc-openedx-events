# swissmooc-openedx-events: agent notes

- **Spec:** `docs/adr/0001-extract-receiver-app-into-pip-package.md` is the
  single source of truth for what to build. The task (what to do now, in which
  order) comes from the prompt. Never edit the ADR.
- **Decisions the ADR does not settle:** do not stop to ask. Choose the option
  that is simplest and consistent with the ADR, record the choice and the
  reason in the ticket's `## Comments`, and continue.
- `bench/` holds the benchmark prompts: never read it for requirements,
  never edit it.
- No emojis in code, docs, or CLI output.
- No host Python. Build, lint, and test run in Docker; expose them as
  `make test` and `make lint`.
- Deps: uv-style `pyproject.toml`; **git-only installs pinned by SemVer tag**;
  never publish to PyPI (name collision with upstream `openedx-events`).
- Django app label is `swissmooc_openedx_events`, never `openedx_events`
  (ADR "Settled decisions" #3).
- Secrets (`SMS_EVENTS_AUTH_TOKEN`, subscriber tokens) come from env /
  ansible-vault; never hardcode or commit.

## Agent skills

### Issue tracker

Local markdown under `.scratch/`; this repo has no remote. Never run `gh`.
See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary, label string == role name. See
`docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` (if present) + `docs/adr/` at the repo root.
See `docs/agents/domain.md`.
