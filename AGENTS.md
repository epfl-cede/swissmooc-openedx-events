# swissmooc-openedx-events — agent notes

- **Current state: design only.** The single source of truth is
  `docs/adr/0001-extract-receiver-app-into-pip-package.md` (decisions only —
  implementation is specified elsewhere). Do not implement anything not
  covered by the ADR; if a decision is missing, ask.
- **Reference implementation** (read-only): `swissmooc-extras`'s
  `src/backend/apps/openedx_events/`. Port behavior, not import paths.
- No emojis in code, docs, or CLI output.
- Tests/lint run via Docker (`make test`, `make lint` once the Makefile
  exists) — no host language tooling available.
- Deps: uv-style `pyproject.toml`; **git-only installs pinned by SemVer tag**;
  never publish to PyPI (name collision with upstream `openedx-events`).
- Django app label is `swissmooc_openedx_events` — never `openedx_events`
  (see ADR section "Settled decisions" #3).
- Secrets (`SMS_EVENTS_AUTH_TOKEN`, subscriber tokens) come from env /
  ansible-vault — never hardcode or commit.

## Agent skills

### Issue tracker

Local markdown under `.scratch/` (overrides the workspace-root GitHub
tracker; this repo has no remote). See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary, label string == role name. See
`docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` (if present) + `docs/adr/` at the repo root.
See `docs/agents/domain.md`.
