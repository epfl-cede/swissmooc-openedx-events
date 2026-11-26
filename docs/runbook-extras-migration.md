# swissmooc-extras: openedx-events migration runbook

This runbook switches swissmooc-extras from its local
`apps.openedx_events` app to this package. It is written from the extras
reference checkout and the ADR (decision 6); it is not executed by this
pipeline and does not touch the extras repo.

Target schema facts:

- Old table: `openedx_events_openedxevent` (extras migration `0001_initial`).
- New table: `swissmooc_openedx_events_openedxevent` (this package's fresh
  `0001_initial`).
- Both tables have the same columns: `id`, `event_id` (unique),
  `event_type`, `course_key`, `org`, `course`, `run`, `instance_name`,
  `occurred_at`, `received_at`. `occurred_at` and `received_at` both exist
  in the old table (extras' `0002_migrate_course_publish_events` fills
  them).

Order of operations: deploy the code and apply migrations first, then copy
rows, then drop the old app. Until step (b) completes, consumers reading the
new table see no history.

## 1. Install and migrate

Add the package as a git-only dependency pinned by SemVer tag, add
`"swissmooc_openedx_events"` to `INSTALLED_APPS`, and include its URLconf
with `path("api/v1/", include("swissmooc_openedx_events.urls"))` as
described in the package `README.md`.

Apply migrations:

```bash
python manage.py migrate swissmooc_openedx_events
```

This creates `swissmooc_openedx_events_openedxevent`. The old
`openedx_events_openedxevent` table is left in place for the copy below.

## 2. Copy rows from the old table

Run this against the MySQL database. `INSERT IGNORE` keeps the copy
idempotent: `event_id` is unique, so a row whose `event_id` already exists
in the new table is skipped.

```sql
INSERT IGNORE INTO swissmooc_openedx_events_openedxevent
    (id, event_id, event_type, course_key, org, course, run,
     instance_name, occurred_at, received_at)
SELECT id, event_id, event_type, course_key, org, course, run,
       instance_name, occurred_at, received_at
FROM openedx_events_openedxevent;
```

After the copy, spot-check counts and the dedupe key:

```sql
SELECT COUNT(*) FROM openedx_events_openedxevent;
SELECT COUNT(*) FROM swissmooc_openedx_events_openedxevent;
SELECT COUNT(*), COUNT(DISTINCT event_id)
FROM swissmooc_openedx_events_openedxevent;
```

The last query should show `COUNT(*) = COUNT(DISTINCT event_id)`.

## 3. Remove the old app, keep the table, then drop it

Remove the local `apps.openedx_events` from code: delete the module, drop
its `INSTALLED_APPS` entry, its URL include, and its dependency/imports. Do
not add a destructive migration yet: keep `openedx_events_openedxevent` for
one release cycle so a rollback can read it.

After the new table has served one release cycle without issue, drop the old
table:

```sql
DROP TABLE openedx_events_openedxevent;
```
