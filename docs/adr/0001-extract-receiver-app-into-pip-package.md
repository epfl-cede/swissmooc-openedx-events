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

## Consequences

- Distribution installs are git-only by tag; the PyPI name collision with the
  upstream library is avoided by the `swissmooc-` prefix.
- extras' event history survives via the copy step; until runbook step (b)
  runs, consumers reading the new table see no history (e.g.
  `course_xml_dump` treats all courses as not republished — dumps resume on
  next publish).
