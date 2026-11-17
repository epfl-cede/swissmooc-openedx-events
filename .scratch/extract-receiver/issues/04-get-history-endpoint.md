# 04 - GET history endpoint behind per-host opt-in

Status: ready-for-agent
Blocked by: 03-post-ingest-endpoint.md

## What it delivers

The read half of the wire contract: `GET` on the same `events/` view,
opt-in per host. Demoable with curl in Docker, both with the flag on and off.

## Deliverables

- `GET` added to ticket 03's existing `events/` view, reusing its auth
  check (no second copy of the auth logic).
- `OPENEDX_EVENTS_SERVE_HISTORY` setting: when unset/False, GET answers 404
  whatever the credentials (ADR decision 7). When True: after authentication,
  200 with a JSON list, newest `occurred_at` first, each item carrying `id`,
  `event_id`, `event_type`, `course_key`, `org`, `course`, `run`,
  `instance_name`, `occurred_at`, `received_at`.
- Optional query filters: `course_key` (exact), `instance_name`
  (case-insensitive), `event_type` (exact).
- Tests at the endpoint seam: 404-when-disabled for all credential states
  (including a correct token), 200 shape and ordering, each filter, filter
  combinations, empty result.

## Acceptance

- `make test lint` green; flag-off/flag-on behavior fully covered.
