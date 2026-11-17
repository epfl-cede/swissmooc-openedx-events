# Extract the openedx-events webhook receiver from swissmooc-extras into a standalone pip package

## Context and decision

swissmooc-extras' `apps.openedx_events` (webhook endpoint + `OpenedxEvent`
store) is the reference implementation for catching `course_published` events
from the `platform-plugin-sms-events` CMS plugin. swissmooc-catalog needs the
same capability. Decision: extract the app into a standalone pip package,
repo `git@github.com:epfl-cede/swissmooc-openedx-events.git`, and switch
extras to depend on the package instead of keeping its own copy — one
implementation, no drift between near-twin repos.

We deliberately do **not** use the upstream `openedx-events` library or an
event bus (Kafka/Redis): the existing, proven mechanism is in-process CMS
signals (`xmodule.modulestore.django.SignalHandler.course_published`) fanned
out by the plugin over bearer-token HTTP webhooks; the deployment stack has no
event-bus infrastructure.

## Settled decisions (grilling session, 2026)

1. **Scope: receiver side only.** The extracted package is the webhook
   receiver + event store. The CMS plugin (`platform-plugin-sms-events`)
   stays as-is.
2. **Consumers: catalog + extras.** Extras deletes its local
   `apps.openedx_events` and depends on the package. Insights: not in scope.
3. **Naming.** Distribution and repo: `swissmooc-openedx-events`. Django app
   label and module: `swissmooc_openedx_events` (deliberately NOT
   `openedx_events` — PyPI name `openedx-events` belongs to the upstream
   event-bus library).
4. **Repo: standalone** `epfl-cede/swissmooc-openedx-events`, private.
5. **Install: git-only, pinned by SemVer tag** (e.g.
   `swissmooc-openedx-events @ git+https://github.com/epfl-cede/swissmooc-openedx-events.git@v0.1.0`).
   No PyPI publish.
6. **Migrations: fresh `0001` under the new label.** Consequence for extras:
   its existing `openedx_events_openedxevent` table is orphaned; deploy
   runbook must (a) apply migrations (creates
   `swissmooc_openedx_events_openedxevent`), (b) copy rows
   (`INSERT IGNORE ... SELECT` on MySQL), (c) remove the old app and keep the
   old table for one release cycle, then drop it. Catalog and insights are
   greenfield: plain `migrate`.
7. **GET history is opt-in per host.** Package ships the `GET` query endpoint
   but it 404s unless the host sets `OPENEDX_EVENTS_SERVE_HISTORY = True`.
   Catalog keeps it disabled (public, paid-enrollment site; no consumer of
   GET today). Extras sets it to keep parity.
8. **Packaging: AppConfig + documented URL include.** Package provides
   `AppConfig` (registers admin) and a one-line include for hosts:
   `path("api/v1/", include("swissmooc_openedx_events.urls"))`. Hosts keep
   only the include line plus `SMS_EVENTS_AUTH_TOKEN` in settings.
9. **Catalog consumer behavior: storage only for now** — persist events,
   dedupe by `event_id`, no feature wired, no admin beyond what the package
   registers.
10. **Python support: `>=3.11`.** Django `>=4.2`, djangorestframework
    `>=3.14` (works on extras' Django 5.2 stack).
11. **CMS fan-out into catalog (second `SMS_EVENTS` subscriber entry per
    instance, vault-configured) is a follow-up change**, out of scope here.
12. **Catalog consumer wiring** (INSTALLED_APPS entry, URL include,
    `SMS_EVENTS_AUTH_TOKEN` via django-configurations, uv git dep in
    `src/backend/pyproject.toml`) is part of the implementation task.

## Webhook contract (binding)

The package must keep the wire and data contract of the extras app unchanged,
so the CMS plugin and existing consumers keep working.

**Endpoint.** One view at `events/` inside the package URLconf, so with the
documented include it is served at `/api/v1/events/`. It accepts `POST`
(ingest) and `GET` (history, decision 7).

**Authentication** (both methods, checked before anything else):

| Condition | Status |
|---|---|
| `SMS_EVENTS_AUTH_TOKEN` unset or empty | 503 |
| no `Authorization` header, or scheme is not `Bearer` | 401 |
| bearer token differs from `SMS_EVENTS_AUTH_TOKEN` (constant-time compare) | 403 |

DRF authentication and permission classes are not used for this view.

**POST payload** (JSON object, all fields strings, all required):

| Field | Meaning |
|---|---|
| `event_id` | unique id stamped by the plugin (a UUID); dedupe key, max 64 chars |
| `event_type` | e.g. `course_published`; max 64 chars |
| `occurred_at` | ISO 8601 datetime |
| `course_key` | e.g. `course-v1:EPFL+DemoX+2025_T1`; max 255 chars |
| `org`, `course`, `run` | parts of the course key; max 255 chars each |
| `instance_name` | Open edX instance (tenant), e.g. `epfl`; max 64 chars |

**POST behavior:**

- Missing or empty `event_type`: 400, nothing stored.
- `event_type == "course_published"`: validate all fields (any missing field or
  unparseable `occurred_at` is 400, nothing stored), then store. A repeated
  `event_id` stores nothing new and answers as if it had been stored, with the
  existing row's `id`. Response 202, body
  `{"status": "accepted", "id": <row id>, "event_id": ..., "event_type": ...}`.
- Any other `event_type`: 202 `{"status": "accepted", "event_type": ...}`,
  nothing stored (accepted as a no-op so the plugin does not retry).

**GET behavior** (only when `OPENEDX_EVENTS_SERVE_HISTORY = True`, otherwise
404 whatever the credentials): after authentication, 200 with a JSON list of
events, newest `occurred_at` first, each item carrying `id`, `event_id`,
`event_type`, `course_key`, `org`, `course`, `run`, `instance_name`,
`occurred_at`, `received_at`. Optional query filters: `course_key` (exact),
`instance_name` (case-insensitive), `event_type` (exact).

**Model** `OpenedxEvent` (table `swissmooc_openedx_events_openedxevent`):
the payload fields above (`event_id` unique, `occurred_at` a datetime) plus
`received_at` set on insert. Default ordering newest `occurred_at` first.
Its default manager provides the two query methods existing consumers call
(extras' `course_xml_dump`):

- `course_published_for_organisation(instance_name)`: all `course_published`
  events of that instance, instance matched case-insensitively.
- `latest_course_publish(course_key, instance_name)`: the newest
  `course_published` event for that course and instance, or `None`.

**Admin:** the package registers `OpenedxEvent` in the Django admin, read-only
fields, searchable by course key, org, course, run, instance, and event id.

## Consequences

- Distribution installs are git-only by tag; the PyPI name collision with the
  upstream library is avoided by the `swissmooc-` prefix.
- extras' event history survives via the copy step; until runbook step (b)
  runs, consumers reading the new table see no history (e.g.
  `course_xml_dump` treats all courses as not republished — dumps resume on
  next publish).
