# 01 - Scaffold package, Docker toolchain, green pipeline

Status: ready-for-agent

## What it delivers

The repo is a runnable, installable Django package skeleton with a fully
Docker-based toolchain: `make test` and `make lint` pass on a clean checkout
with no host Python or Node.

## Deliverables

- `pyproject.toml` (uv style): distribution `swissmooc-openedx-events`,
  `requires-python >= 3.11`, deps `Django>=4.2`,
  `djangorestframework>=3.14`. Metadata documents the git-only install
  convention (e.g. the `v0.1.0` install line from ADR decision 5) and that
  the package is never published to PyPI. No dev-only deps outside an
  optional dependency group.
- Package module `swissmooc_openedx_events/` with `apps.py`
  (`SwissmoocOpenedxEventsConfig`, default auto field, label
  `swissmooc_openedx_events`) and an empty `urls.py` with a docstring noting
  the documented host include
  `path("api/v1/", include("swissmooc_openedx_events.urls"))`.
- `Makefile` at repo root with at least: `test`, `lint`, `acceptance`
  (stub ok for now, real in ticket 05), `shell`. Every target runs in Docker
  (one-shot container, project root volume-mounted, `/workspace` workdir;
  Dockerfile or inline `docker run` — simplest option that works, recorded in
  `## Comments`). No host-interpreter fallbacks.
- Minimal test settings/test project fixture (a tiny `tests/` Django settings
  module with the app in `INSTALLED_APPS`) proving the AppConfig installs.
- One smoke test: app imports, AppConfig label is
  `swissmooc_openedx_events`.
- `make lint` wired to something real (ruff is fine) via Docker.

## Out of scope

Model, views, admin (later tickets). CI config (no remote exists).

## Acceptance

- Fresh clone + `make test lint` green in Docker.
- No command in the repo requires host Python.
