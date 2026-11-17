# swissmooc-openedx-events

Reusable, pip-installable Django app that receives `course_published` webhooks
from the [`platform-plugin-sms-events`](https://github.com/epfl-cede/platform-plugin-sms-events)
CMS plugin and stores them in a durable, deduplicated event table.

**Status: design only.** The spec is
`docs/adr/0001-extract-receiver-app-into-pip-package.md` (settled decisions:
scope, naming, migrations, gating).

## Install (once it exists)

Git-only, pinned by SemVer tag (private repo; PyPI name `openedx-events` is
taken by the upstream event-bus library):

```toml
"swissmooc-openedx-events @ git+https://github.com/epfl-cede/swissmooc-openedx-events.git@v0.1.0",
```

## Consumers

- swissmooc-extras: switches from its local `apps.openedx_events` (runbook in the ADR)
- swissmooc-catalog: new consumer, storage only, GET history disabled
