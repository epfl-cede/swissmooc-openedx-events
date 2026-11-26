from datetime import UTC, datetime

from django.db import IntegrityError, connection, transaction
from django.db.migrations.loader import MigrationLoader
from django.test import TestCase

from swissmooc_openedx_events.models import OpenedxEvent


def create_event(**overrides):
    payload = {
        "event_id": "11111111-1111-1111-1111-111111111111",
        "event_type": "course_published",
        "occurred_at": datetime(2026, 1, 1, tzinfo=UTC),
        "course_key": "course-v1:EPFL+DemoX+2025_T1",
        "org": "EPFL",
        "course": "DemoX",
        "run": "2025_T1",
        "instance_name": "epfl",
    }
    payload.update(overrides)
    return OpenedxEvent.objects.create(**payload)


class OpenedxEventModelTest(TestCase):
    def test_received_at_is_stamped_on_insert(self):
        event = create_event()
        self.assertIsNotNone(event.received_at)

    def test_event_id_is_unique(self):
        create_event(event_id="same-id")
        with self.assertRaises(IntegrityError), transaction.atomic():
            create_event(event_id="same-id")

    def test_default_ordering_is_newest_occurred_at_first(self):
        older = create_event(
            event_id="older",
            occurred_at=datetime(2025, 1, 1, tzinfo=UTC),
        )
        newer = create_event(
            event_id="newer",
            occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        self.assertEqual(list(OpenedxEvent.objects.all()), [newer, older])

    def test_course_published_for_organisation(self):
        create_event(event_id="published", instance_name="epfl")
        create_event(event_id="other-type", instance_name="epfl", event_type="other")
        create_event(event_id="other-instance", instance_name="unige")
        self.assertEqual(
            list(OpenedxEvent.objects.course_published_for_organisation("epfl")),
            [OpenedxEvent.objects.get(event_id="published")],
        )

    def test_course_published_for_organisation_matches_instance_case_insensitively(self):
        create_event(event_id="published", instance_name="epfl")
        self.assertEqual(
            OpenedxEvent.objects.course_published_for_organisation("EPFL").count(),
            1,
        )

    def test_latest_course_publish_returns_newest(self):
        create_event(
            event_id="older",
            occurred_at=datetime(2025, 1, 1, tzinfo=UTC),
        )
        newer = create_event(
            event_id="newer",
            occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        self.assertEqual(
            OpenedxEvent.objects.latest_course_publish(
                "course-v1:EPFL+DemoX+2025_T1", "epfl"
            ),
            newer,
        )

    def test_latest_course_publish_returns_none_when_absent(self):
        self.assertIsNone(
            OpenedxEvent.objects.latest_course_publish("course-v1:EPFL+Missing+2025_T1", "epfl")
        )

    def test_composite_index_is_present_in_migration(self):
        loader = MigrationLoader(connection, ignore_no_migrations=True)
        migration = loader.disk_migrations[("swissmooc_openedx_events", "0001_initial")]
        create_model = next(
            op for op in migration.operations if op.__class__.__name__ == "CreateModel"
        )
        index_fields = [tuple(index.fields) for index in create_model.options["indexes"]]
        self.assertIn(("course_key", "instance_name", "-occurred_at"), index_fields)
