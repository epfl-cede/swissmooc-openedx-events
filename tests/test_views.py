import secrets
from datetime import UTC, datetime
from typing import Any
from unittest import mock

from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.urls import reverse

from swissmooc_openedx_events.models import OpenedxEvent

AUTH_TOKEN = secrets.token_urlsafe(32)
EVENTS_URL = "/api/v1/events/"


REQUIRED_FIELDS = (
    "event_id",
    "event_type",
    "occurred_at",
    "course_key",
    "org",
    "course",
    "run",
    "instance_name",
)

def authorized_post(client, data=None, token=AUTH_TOKEN):
    extra = {"content_type": "application/json"}
    if token is not None:
        extra["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    return client.post(EVENTS_URL, data=data, **extra)


def course_published_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "event_id": "11111111-1111-1111-1111-111111111111",
        "event_type": "course_published",
        "occurred_at": "2026-01-01T00:00:00Z",
        "course_key": "course-v1:EPFL+DemoX+2025_T1",
        "org": "EPFL",
        "course": "DemoX",
        "run": "2025_T1",
        "instance_name": "epfl",
    }
    payload.update(overrides)
    return payload


class EventsUrlTest(TestCase):
    def test_events_url_reverses_with_app_name(self):
        self.assertEqual(reverse("swissmooc_openedx_events:events"), EVENTS_URL)


@override_settings(SMS_EVENTS_AUTH_TOKEN=AUTH_TOKEN)
class EventsPostAuthTest(TestCase):
    def test_missing_authorization_header_returns_401(self):
        response = self.client.post(
            EVENTS_URL, data={}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(OpenedxEvent.objects.count(), 0)

    def test_non_bearer_scheme_returns_401(self):
        response = self.client.post(
            EVENTS_URL,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Basic {AUTH_TOKEN}",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(OpenedxEvent.objects.count(), 0)

    def test_wrong_token_returns_403(self):
        response = self.client.post(
            EVENTS_URL,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer wrong-token",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(OpenedxEvent.objects.count(), 0)

    def test_valid_token_passes_auth(self):
        response = authorized_post(
            self.client, data={"event_type": "some_event"}
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["status"], "accepted")


class EventsPostUnconfiguredTokenTest(TestCase):
    def test_unset_token_returns_503(self):
        response = self.client.post(
            EVENTS_URL, data={}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(OpenedxEvent.objects.count(), 0)

    @override_settings(SMS_EVENTS_AUTH_TOKEN="")
    def test_empty_token_returns_503(self):
        response = self.client.post(
            EVENTS_URL, data={}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(OpenedxEvent.objects.count(), 0)


@override_settings(SMS_EVENTS_AUTH_TOKEN=AUTH_TOKEN)
class EventsPostBodyValidationTest(TestCase):
    def test_invalid_json_returns_400(self):
        response = authorized_post(self.client, data='{"invalid"')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(OpenedxEvent.objects.count(), 0)

    def test_json_list_returns_400(self):
        response = authorized_post(self.client, data=[1, 2, 3])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(OpenedxEvent.objects.count(), 0)

    def test_json_scalar_number_returns_400(self):
        response = authorized_post(self.client, data=42)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(OpenedxEvent.objects.count(), 0)

    def test_json_scalar_string_returns_400(self):
        response = authorized_post(self.client, data='"hello"')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(OpenedxEvent.objects.count(), 0)

    def test_json_null_returns_400(self):
        response = authorized_post(self.client, data="null")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(OpenedxEvent.objects.count(), 0)

    def test_missing_event_type_returns_400(self):
        response = authorized_post(self.client, data={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(OpenedxEvent.objects.count(), 0)

    def test_empty_event_type_returns_400(self):
        response = authorized_post(self.client, data={"event_type": ""})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(OpenedxEvent.objects.count(), 0)

    def test_non_string_event_type_returns_400(self):
        response = authorized_post(self.client, data={"event_type": 7})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(OpenedxEvent.objects.count(), 0)

    def test_unknown_event_type_is_accepted_as_noop(self):
        response = authorized_post(self.client, data={"event_type": "other_event"})
        self.assertEqual(response.status_code, 202)
        self.assertEqual(
            response.json(),
            {"status": "accepted", "event_type": "other_event"},
        )
        self.assertEqual(OpenedxEvent.objects.count(), 0)


@override_settings(SMS_EVENTS_AUTH_TOKEN=AUTH_TOKEN)
class EventsPostCoursePublishedTest(TestCase):
    def test_course_published_stores_event_and_returns_202(self):
        payload = course_published_payload()
        response = authorized_post(self.client, data=payload)

        self.assertEqual(response.status_code, 202)
        event = OpenedxEvent.objects.get(event_id=payload["event_id"])
        self.assertEqual(
            response.json(),
            {
                "status": "accepted",
                "id": event.id,
                "event_id": payload["event_id"],
                "event_type": "course_published",
            },
        )
        self.assertEqual(event.occurred_at, datetime(2026, 1, 1, tzinfo=UTC))
        self.assertEqual(event.course_key, payload["course_key"])
        self.assertIsNotNone(event.received_at)

    def test_course_published_deduplicates_by_event_id(self):
        payload = course_published_payload()
        first = authorized_post(self.client, data=payload)
        second = authorized_post(self.client, data=payload)

        self.assertEqual(first.status_code, 202)
        self.assertEqual(second.status_code, 202)
        self.assertEqual(first.json()["id"], second.json()["id"])
        self.assertEqual(OpenedxEvent.objects.count(), 1)

    def test_course_published_missing_field_returns_400(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(field=field):
                payload = course_published_payload()
                payload.pop(field)
                response = authorized_post(self.client, data=payload)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(OpenedxEvent.objects.count(), 0)

    def test_course_published_numeric_field_is_coerced_to_string(self):
        """DRF CharFields stringify numbers, matching extras' behavior."""
        for field in ("event_id", "course_key", "org", "course", "run", "instance_name"):
            with self.subTest(field=field):
                payload = course_published_payload()
                if field != "event_id":
                    payload["event_id"] = f"numeric-{field}"
                payload[field] = 7
                response = authorized_post(self.client, data=payload)
                self.assertEqual(response.status_code, 202)
                event_id = "7" if field == "event_id" else payload["event_id"]
                event = OpenedxEvent.objects.get(event_id=event_id)
                self.assertEqual(getattr(event, field), "7")

    def test_course_published_numeric_occurred_at_returns_400(self):
        payload = course_published_payload(occurred_at=7)
        response = authorized_post(self.client, data=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(OpenedxEvent.objects.count(), 0)

    def test_course_published_empty_field_returns_400(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(field=field):
                payload = course_published_payload()
                payload[field] = ""
                response = authorized_post(self.client, data=payload)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(OpenedxEvent.objects.count(), 0)

    def test_course_published_unparseable_occurred_at_returns_400(self):
        payload = course_published_payload(occurred_at="not-a-datetime")
        response = authorized_post(self.client, data=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(OpenedxEvent.objects.count(), 0)

    def test_course_published_recovers_from_concurrent_insert(self):
        payload = course_published_payload()
        existing = OpenedxEvent.objects.create(
            event_id=payload["event_id"],
            event_type=payload["event_type"],
            occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
            course_key=payload["course_key"],
            org=payload["org"],
            course=payload["course"],
            run=payload["run"],
            instance_name=payload["instance_name"],
        )

        with mock.patch.object(
            OpenedxEvent.objects,
            "get_or_create",
            side_effect=IntegrityError("duplicate"),
        ):
            response = authorized_post(self.client, data=payload)

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["id"], existing.id)
        self.assertEqual(OpenedxEvent.objects.count(), 1)
