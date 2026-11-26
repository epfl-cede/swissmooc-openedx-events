# Changelog

## v0.1.0

Initial extraction of the openedx-events webhook receiver from
swissmooc-extras into a standalone, git-only Django package.

- Webhook receiver at `/api/v1/events/` (with the documented include):
  bearer-token auth, `course_published` POST ingest with dedupe on
  `event_id`, no-op accept for unknown event types, and opt-in GET history
  behind `OPENEDX_EVENTS_SERVE_HISTORY`.
- `OpenedxEvent` model (table
  `swissmooc_openedx_events_openedxevent`) with
  `course_published_for_organisation` and `latest_course_publish` manager
  methods.
- Read-only, searchable `OpenedxEvent` Django admin.
- `SwissmoocOpenedxEventsConfig` with app label
  `swissmooc_openedx_events`.
- `make test` and `make lint` run entirely in Docker.

Install (git-only, pinned by SemVer tag):

```toml
"swissmooc-openedx-events @ git+https://github.com/epfl-cede/swissmooc-openedx-events.git@v0.1.0",
```
