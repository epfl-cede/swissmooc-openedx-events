# Spec: Extract the openedx-events webhook receiver into a standalone pip package

Source of truth for the contract: `docs/adr/0001-extract-receiver-app-into-pip-package.md`.
This file is a pointer + summary, plus the scope of this pipeline. The ADR
is never edited. On the package's wire and data contract, the ADR wins over
this file; on what this pipeline builds (scope), this file decides (per
AGENTS.md, the task comes from the prompt, not the ADR).

## What we build

Repo `swissmooc-openedx-events` becomes a standalone, git-only (SemVer-tag
pinned, never PyPI) Django package providing the webhook receiver + event
store extracted from swissmooc-extras' `apps.openedx_events`.

- Distribution / repo: `swissmooc-openedx-events`
- Django app label and module: `swissmooc_openedx_events` (never
  `openedx_events`: PyPI name collision with the upstream event-bus library)
- Intended consumers (context only, not wired here): swissmooc-catalog and
  swissmooc-extras.
- Python `>=3.11`, Django `>=4.2`, djangorestframework `>=3.14`.
- Packaging: `AppConfig` (registers admin) + one-line URL include for hosts:
  `path("api/v1/", include("swissmooc_openedx_events.urls"))`.
  Hosts configure only the include + `SMS_EVENTS_AUTH_TOKEN`.
- GET history is opt-in per host: `OPENEDX_EVENTS_SERVE_HISTORY = True`.
- Extras migration runbook (ADR decision 6) ships as a doc in this repo;
  this pipeline writes it but does not execute it.

## Binding wire and data contract

Fully specified in the ADR section "Webhook contract (binding)": endpoint
`events/` (served at `/api/v1/events/` with the documented include), auth
matrix (503 / 401 / 403 with constant-time compare, DRF auth/permissions NOT
used), POST payload table and behavior (400 on missing/invalid for
`course_published`, dedupe on `event_id`, 202 no-op for other event types),
GET behavior behind the opt-in flag with three filters, `OpenedxEvent` model
(table `swissmooc_openedx_events_openedxevent`, unique `event_id`,
`received_at` on insert, newest-`occurred_at`-first ordering), the two
manager query methods (`course_published_for_organisation(instance_name)`,
`latest_course_publish(course_key, instance_name)`), and the read-only
searchable admin.

## Decisions taken for this pipeline

- Database for tests and acceptance: SQLite only in v1. Because SQLite does
  not enforce `max_length`, length limits must be enforced in the view's
  validation (ticket 03), not left to the database.
- Release tag is per run (`<run>/v0.1.0`, see YOLO.md); the README install
  line shows the canonical `v0.1.0` that a human cuts later.

## Decisions the ADR does not settle

Per repo AGENTS.md: do not stop to ask. Choose the simplest option consistent
with the ADR, record the choice and reason in the ticket's `## Comments`, and
continue.

## Scope boundaries

Deliberately out of scope for this pipeline (operator decision), even
though the ADR describes them:

- Extras switch-over (ADR decision 2 / 6 consumer side): no edits to the
  extras repo.
- Catalog consumer wiring (ADR decision 12): no edits to the catalog repo.
- CMS plugin (`platform-plugin-sms-events`): unchanged.
- CMS fan-out second subscriber entry for catalog (ADR decision 11).
- The ADR is never edited. New decisions go in ticket `## Comments`.
