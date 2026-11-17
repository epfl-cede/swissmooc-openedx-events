# YOLO: standing answers for autonomous execution

This file removes every human gate from the skills used by this pipeline.
An agent running this pipeline must not stop to ask the user anything.
Read this file before invoking any skill.

## Run identity (do this first)

Several runs of this pipeline (one per VM) are compared afterwards, so every
ref a run creates lives under its own namespace and never collides with
another run's refs when the results are collected into one repo.

- `RUN` is the suffix of the VM name: `RUN=$(hostname -s | sed 's/.*-//')`.
  It must be one of `glm`, `claude`, `kimi`, `deepseek`; otherwise stop and
  report (this is the only allowed stop).
- Integration branch: `$RUN/extract-receiver`, created from `master`.
- Ticket branches: `$RUN/<NN>-<slug>` (e.g. `claude/03-post-ingest-endpoint`).
- Ticket worktrees: `~/src/wt/$RUN/<NN>-<slug>` (outside the repo dir, so
  repo tooling never picks them up).
- Release tag: `$RUN/v0.1.0`, annotated, message
  "swissmooc-openedx-events v0.1.0 ($RUN run)".
- Never commit to `master`. Never create, move, or delete any branch or tag
  outside the `$RUN/` namespace (in particular, never create a bare `v0.1.0`
  tag: the canonical tag is cut later by a human from the chosen run).

## Workflow

Implement the ticket graph in `.scratch/extract-receiver/issues/` following
the `implement-spec` workflow:

- One fresh implementer subagent per ticket, in its own worktree on its own
  ticket branch, based on the integration branch tip.
- Each implementer uses the `tdd` skill: red, green, minimal, one slice at a
  time. Commit per slice with a message referencing the ticket file.
- Merge to the integration branch after each ticket closes.
- The graph is linear: 01 -> 02 -> 03 -> 04 -> 05.
- When all tickets are done, run the `code-review` skill on the integration
  branch (see fixed point below) and fix its findings with one fresh
  implementer subagent: every documented-standard violation and every spec
  finding gets fixed; baseline smells (judgement calls) are fixed or
  declined, each declined one recorded with its reason in the relevant
  ticket's `## Comments`. Re-run `make test lint acceptance`, then tag
  `$RUN/v0.1.0` on the integration branch tip. Tagging is pre-approved; do
  not ask.

## Standing answers (override skill defaults that normally quiz the user)

1. **to-tickets**: the breakdown in `issues/` is final and pre-approved.
   Never re-quiz on granularity or edges. If a ticket turns out wrong, fix
   the ticket file and continue; record why in its `## Comments`.
2. **tdd seams**: pre-agreed. The seams are exactly the ADR "Webhook
   contract (binding)" section: the `events/` endpoint (auth matrix, POST
   behavior, GET behavior), the `OpenedxEvent` model + its two manager query
   methods, and the admin registration. Test at those seams only. Do not ask
   for confirmation; this file is the confirmation.
3. **code-review fixed point**: `master`
   (`git diff master...$RUN/extract-receiver`). Never ask.
4. **Unsettled decisions**: per repo AGENTS.md: never ask. Pick the option
   that is simplest and consistent with the ADR, record choice + reason in
   the ticket's `## Comments`, continue.
5. **Ticket closure**: set `Status: done` in the ticket file, append a
   `## Comments` entry naming the commit SHA(s) that resolved it. That is the
   entire close ritual; no PR, no remote, no `gh` (this repo has none).
6. **Definition of done for the whole pipeline**: all five ticket files
   (01-05) `Status: done`, `make test lint acceptance` green on
   `$RUN/extract-receiver`, annotated tag `$RUN/v0.1.0` on its tip. Report
   and stop.

## Hard rules (from repo AGENTS.md: restate, non-negotiable)

- Never edit `docs/adr/0001-extract-receiver-app-into-pip-package.md` or
  anything under `bench/`.
- Never read `bench/` for requirements.
- The extras reference implementation is the separate checkout
  `~/src/swissmooc-extras` (from the main checkout: `../swissmooc-extras`;
  from a worktree, always use the absolute `~/src/swissmooc-extras`). The
  module to port is `src/backend/apps/openedx_events/`. It is read-only:
  port semantics from it; never write to it, never commit in it, never copy
  files from it into this repo verbatim.
- No other repo is touched: no catalog or extras wiring in this pipeline.
- No emojis in code, docs, or CLI output.
- No host Python/Node: build, lint, test run in Docker via the Makefile.
  Docker is the agent's only Python/tooling environment on the VM. If a
  tool is missing on the host, it goes through Docker, period.
- Deps: uv-style `pyproject.toml`, git-only installs pinned by SemVer tag,
  never publish to PyPI.
- App label is `swissmooc_openedx_events`, never `openedx_events`.
- No secrets in code or tests: `SMS_EVENTS_AUTH_TOKEN` and subscriber tokens
  are env/vault material; tests generate throwaway values at runtime.
