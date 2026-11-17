# 05 - Release: docs, acceptance gate

Status: ready-for-agent
Blocked by: 03-post-ingest-endpoint.md, 04-get-history-endpoint.md

## What it delivers

The package is releasable: a stranger can install it by git tag, wire it in
two lines, and verify the wire contract mechanically. Tagging is NOT part of
this ticket: the per-run tag is cut by the pipeline after code review (see
YOLO.md).

## Deliverables

- `README.md`: purpose, the git-only install line per ADR decision 5
  (`swissmooc-openedx-events @ git+https://github.com/epfl-cede/swissmooc-openedx-events.git@v0.1.0`),
  AppConfig + `INSTALLED_APPS` entry, the one-line URL include, required
  `SMS_EVENTS_AUTH_TOKEN`, opt-in `OPENEDX_EVENTS_SERVE_HISTORY`, endpoint
  summary (auth matrix, POST/GET behavior) referencing the ADR as binding
  contract, and the manager query methods.
- `CHANGELOG.md` entry for `v0.1.0`.
- `make acceptance`: real implementation now (replacing the ticket-01 stub).
  Spins a throwaway Django project in Docker, applies migrations, runs
  runserver, and curls the contract end to end: full auth matrix (503/401/403
  and success paths), a valid `course_published` POST (202 + stored row via
  GET or ORM), dedupe repeat, unknown event type no-op, 400 paths, GET 404
  with flag off and 200 with flag on. Asserts expected statuses and bodies.
  Exit code is the verdict; no human reads output.
- Host migration runbook doc for extras (ADR decision 6) as
  `docs/runbook-extras-migration.md`: (a) apply migrations (creates
  `swissmooc_openedx_events_openedxevent`), (b) copy rows
  (`INSERT IGNORE ... SELECT` on MySQL), (c) remove old app, keep old table
  one release cycle, then drop. Written from the ADR + extras reference
  checkout (`~/src/swissmooc-extras`); this pipeline does not execute it
  and does not touch the extras repo.

## Acceptance

- `make test lint acceptance` green from a clean worktree.
- README's install line uses the canonical `@v0.1.0` (not the per-run
  tag), matching the `CHANGELOG.md` entry.
