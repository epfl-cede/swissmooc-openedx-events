# swissmooc-openedx-events

Reusable Django app that receives `course_published` webhooks from the
[`platform-plugin-sms-events`](https://github.com/epfl-cede/platform-plugin-sms-events)
CMS plugin and stores them in a durable, deduplicated event table.

The wire and data contract is fixed by
`docs/adr/0001-extract-receiver-app-into-pip-package.md` (section "Webhook
contract (binding)"). Where this README summarises, the ADR is the binding
contract.

## Install

The package is distributed git-only, pinned by SemVer tag. It is never
published to PyPI because the `openedx-events` name there belongs to the
upstream event-bus library.

```toml
"swissmooc-openedx-events @ git+https://github.com/epfl-cede/swissmooc-openedx-events.git@v0.1.0",
```

## Wire it up

Add the app to `INSTALLED_APPS`. The entry
`"swissmooc_openedx_events"` is sufficient: Django discovers
`swissmooc_openedx_events.apps.SwissmoocOpenedxEventsConfig` (app label
`swissmooc_openedx_events`, registers the read-only `OpenedxEvent` admin).

```python
INSTALLED_APPS = [
    # ...
    "swissmooc_openedx_events",
]
```

Include the package URLconf:

```python
from django.urls import include, path

urlpatterns = [
    # ...
    path("api/v1/", include("swissmooc_openedx_events.urls")),
]
```

Configure the shared secret. It is env/vault material; do not commit it.

```python
SMS_EVENTS_AUTH_TOKEN = os.environ["SMS_EVENTS_AUTH_TOKEN"]
```

History serving is opt-in per host:

```python
OPENEDX_EVENTS_SERVE_HISTORY = True  # default is False (GET returns 404)
```

Then apply migrations:

```bash
python manage.py migrate
```

This creates the `swissmooc_openedx_events_openedxevent` table.

## Endpoint

With the documented include, the single view is served at
`/api/v1/events/`. It accepts `POST` (ingest) and `GET` (history).

### Authentication

Both methods authenticate the same way, before anything else:

| Condition | Status |
|---|---|
| `SMS_EVENTS_AUTH_TOKEN` unset or empty | 503 |
| no `Authorization` header, or scheme is not `Bearer` | 401 |
| bearer token differs from `SMS_EVENTS_AUTH_TOKEN` | 403 |

DRF authentication and permission classes are not used for this view.

### POST

`POST` ingests one event. The body is a JSON object.

- `course_published` events are validated field by field; a missing,
  non-string, empty, too-long, or unparseable field is `400` and nothing is
  stored. On success the row is stored and the response is `202` with
  `{"status": "accepted", "id": ..., "event_id": ..., "event_type": ...}`.
- A repeated `event_id` stores nothing new and answers as if it had been
  stored, with the existing row's `id`.
- Any other `event_type` is accepted as a no-op (`202
  {"status": "accepted", "event_type": ...}`) and nothing is stored, so the
  plugin does not retry.

### GET

`GET` returns history only when `OPENEDX_EVENTS_SERVE_HISTORY = True`;
otherwise it returns `404` whatever the credentials. With the flag on and a
valid token it returns `200` with a JSON list of events, newest
`occurred_at` first, each item carrying `id`, `event_id`, `event_type`,
`course_key`, `org`, `course`, `run`, `instance_name`, `occurred_at`, and
`received_at`.

Optional query filters: `course_key` (exact), `instance_name`
(case-insensitive), `event_type` (exact).

## Querying stored events

The default manager exposes two methods that existing consumers call:

```python
from swissmooc_openedx_events.models import OpenedxEvent

OpenedxEvent.objects.course_published_for_organisation("epfl")
OpenedxEvent.objects.latest_course_publish(
    "course-v1:EPFL+DemoX+2025_T1", "epfl"
)
```

- `course_published_for_organisation(instance_name)`: all `course_published`
  events of that instance, matched case-insensitively.
- `latest_course_publish(course_key, instance_name)`: the newest
  `course_published` event for that course and instance, or `None`.

## Consumers

- swissmooc-extras: switches from its local `apps.openedx_events`; see
  `docs/runbook-extras-migration.md`.
- swissmooc-catalog: new consumer, storage only, GET history disabled.
