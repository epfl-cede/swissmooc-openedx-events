# 03 - POST ingest endpoint with auth, validation, dedupe

Status: ready-for-agent
Blocked by: 02-model-managers-admin.md

## What it delivers

The write half of the wire contract: `POST` on `events/` inside the package
URLconf, served at `/api/v1/events/` with the documented include. Demoable
with curl against runserver in Docker.

## Deliverables

- `urls.py` sets `app_name = "swissmooc_openedx_events"` and routes
  `events/` to the view under the name `events`, so hosts using the plain
  documented include can `reverse("swissmooc_openedx_events:events")`.
  The view and its auth check are written so ticket 04 can add `GET` to the
  same view and reuse the auth check unchanged.
- Response contract exactly per the
  ADR "Webhook contract (binding)" section. DRF authentication and permission
  classes are NOT used; auth is checked in the view before anything else:
  - `SMS_EVENTS_AUTH_TOKEN` unset or empty -> 503
  - no `Authorization` header or scheme not `Bearer` -> 401
  - token differs (constant-time compare) -> 403
- POST payload: JSON object, all fields strings, all required
  (`event_id`, `event_type`, `occurred_at`, `course_key`, `org`, `course`,
  `run`, `instance_name`; length limits per ADR).
- Behavior per ADR:
  - missing or empty `event_type` -> 400, nothing stored
  - `course_published` -> validate all fields (missing field or unparseable
    `occurred_at` -> 400, nothing stored), then store; repeated `event_id`
    stores nothing, answers with the existing row's `id`
  - 202 body `{"status": "accepted", "id": ..., "event_id": ...,
    "event_type": ...}`
  - any other `event_type` -> 202 `{"status": "accepted", "event_type":
    ...}`, nothing stored (no-op so the plugin does not retry)
- Validation hardening beyond the extras reference (extras re-declares its
  serializer fields without `max_length`, so over-long values reach the DB
  and fail there; tests run on SQLite, which never enforces length, so the
  view must):
  - body that is not a JSON object (list, scalar, invalid JSON) -> 400,
    nothing stored
  - `event_type` present but not a string -> 400
  - for `course_published`: any field that is not a string, or longer than
    its ADR max length (`event_id`, `event_type`, `instance_name` 64;
    `course_key`, `org`, `course`, `run` 255) -> 400, nothing stored
- Tests at the endpoint seam covering every row of the auth matrix, every
  400 path (including each hardening case above, with a length-limit test
  per field at max and max+1), dedupe (asserts row count unchanged and existing `id`
  returned), and the unknown-event-type no-op.

## Acceptance

- `make test lint` green; auth matrix fully covered by tests.
