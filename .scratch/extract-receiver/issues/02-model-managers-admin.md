# 02 - OpenedxEvent model, migrations, manager query methods, admin

Status: ready-for-agent
Blocked by: 01-scaffold-package-docker.md

## What it delivers

The data layer of the package, contract-identical to extras'
`apps.openedx_events` model: a fresh `0001` migration under the new app
label, the two manager query methods existing consumers call, and the
read-only searchable admin. Demoable by migrating a scratch project and
calling the query methods.

## Deliverables

- `OpenedxEvent` model, table `swissmooc_openedx_events_openedxevent`,
  fields per ADR "Webhook contract (binding)": `event_id` (unique, max 64),
  `event_type` (max 64), `occurred_at` (datetime),
  `course_key`/`org`/`course`/`run` (max 255 each), `instance_name`
  (max 64), `received_at` set on insert. Default ordering newest
  `occurred_at` first, `get_latest_by = "occurred_at"`.
- Indexes carried over from the extras reference (the fresh `0001` is the
  cheap moment to keep them; extras' `course_xml_dump` relies on them):
  `db_index` on `event_type`, `course_key`, `instance_name`, `received_at`,
  plus a composite index on (`course_key`, `instance_name`, `-occurred_at`).
- Fresh migration `0001` under `swissmooc_openedx_events` (ADR decision 6 —
  deliberately not squashed from extras history; the old
  `openedx_events_openedxevent` table stays with extras and is handled by
  its runbook).
- Default manager with exactly the two query methods consumers call
  (reference implementation:
  `~/src/swissmooc-extras/src/backend/apps/openedx_events/models.py`, a
  read-only checkout outside this repo; port semantics, not code, and do
  not write to that checkout):
  - `course_published_for_organisation(instance_name)`: all `course_published`
    events of that instance, instance matched case-insensitively.
  - `latest_course_publish(course_key, instance_name)`: newest
    `course_published` event for that course and instance, or `None`.
- Admin: `OpenedxEvent` registered, read-only, searchable by course key,
  org, course, run, instance, and event id (ADR binding contract).
- Tests at the model seam: insert behavior (`received_at` stamped), unique
  constraint, ordering, indexes present in the migration, both query methods including the case-insensitive
  instance match and the `None` case.

## Acceptance

- `make test lint` green.
- `makemigrations --check` clean (migration exists and is complete).
