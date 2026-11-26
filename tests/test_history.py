import secrets
from datetime import UTC, datetime

from django.test import TestCase, override_settings

from swissmooc_openedx_events.models import OpenedxEvent

AUTH_TOKEN = secrets.token_urlsafe(32)
EVENTS_URL = "/api/v1/events/"

EXPECTED_KEYS = {
    "id",
    "event_id",
    "event_type",
    "course_key",
    "org",
    "course",
    "run",
    "instance_name",
    "occurred_at",
    "received_at",
}


def create_event(**overrides):
    payload = {
        "event_id": "00000000-0000-0000-0000-000000000000",
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


def authorized_get(client, query=None, token=AUTH_TOKEN):
    headers = {} if token is None else {"HTTP_AUTHORIZATION": f"Bearer {token}"}
    return client.get(EVENTS_URL, query or {}, **headers)


@override_settings(SMS_EVENTS_AUTH_TOKEN=AUTH_TOKEN)
class EventsHistoryFlagOffTest(TestCase):
    """GET 404s before auth when the history flag is unset or falsy."""

    def _assert_disabled(self):
        credential_states = [
            ("no header", {}),
            ("wrong scheme", {"HTTP_AUTHORIZATION": f"Basic {AUTH_TOKEN}"}),
            ("wrong token", {"HTTP_AUTHORIZATION": "Bearer wrong-token"}),
            ("correct token", {"HTTP_AUTHORIZATION": f"Bearer {AUTH_TOKEN}"}),
        ]
        for label, extra in credential_states:
            with self.subTest(credential=label):
                response = self.client.get(EVENTS_URL, **extra)
                self.assertEqual(response.status_code, 404)

    def test_unset_flag_returns_404_for_every_credential_state(self):
        self._assert_disabled()

    @override_settings(OPENEDX_EVENTS_SERVE_HISTORY=False)
    def test_false_flag_returns_404_for_every_credential_state(self):
        self._assert_disabled()


class EventsHistoryFlagOffWithoutTokenTest(TestCase):
    """The flag check runs first: no configured token still yields 404."""

    def test_unset_flag_returns_404_when_token_unset(self):
        response = self.client.get(EVENTS_URL)
        self.assertEqual(response.status_code, 404)

    @override_settings(OPENEDX_EVENTS_SERVE_HISTORY=False)
    def test_false_flag_returns_404_when_token_unset(self):
        response = self.client.get(EVENTS_URL)
        self.assertEqual(response.status_code, 404)


@override_settings(
    SMS_EVENTS_AUTH_TOKEN=AUTH_TOKEN,
    OPENEDX_EVENTS_SERVE_HISTORY=True,
)
class EventsHistoryFlagOnTest(TestCase):
    def test_correct_token_returns_200_list_with_full_shape(self):
        event = create_event()
        response = authorized_get(self.client)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

        item = data[0]
        self.assertEqual(set(item.keys()), EXPECTED_KEYS)
        self.assertEqual(item["id"], event.id)
        self.assertEqual(item["event_id"], event.event_id)
        self.assertEqual(item["event_type"], "course_published")
        self.assertEqual(item["course_key"], "course-v1:EPFL+DemoX+2025_T1")
        self.assertEqual(item["org"], "EPFL")
        self.assertEqual(item["course"], "DemoX")
        self.assertEqual(item["run"], "2025_T1")
        self.assertEqual(item["instance_name"], "epfl")
        self.assertIsInstance(item["occurred_at"], str)
        self.assertIsInstance(item["received_at"], str)
        datetime.fromisoformat(item["occurred_at"])
        datetime.fromisoformat(item["received_at"])

    def test_orders_newest_occurred_at_first(self):
        newer = create_event(
            event_id="newer",
            occurred_at=datetime(2026, 1, 3, tzinfo=UTC),
        )
        older = create_event(
            event_id="older",
            occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        middle = create_event(
            event_id="middle",
            occurred_at=datetime(2026, 1, 2, tzinfo=UTC),
        )

        response = authorized_get(self.client)

        self.assertEqual(response.status_code, 200)
        event_ids = [item["event_id"] for item in response.json()]
        self.assertEqual(event_ids, [newer.event_id, middle.event_id, older.event_id])

    def test_filters_by_course_key_exactly(self):
        create_event(event_id="epfl", course_key="course-v1:EPFL+DemoX+2025_T1")
        create_event(event_id="ethz", course_key="course-v1:ETHZ+OtherX+2025_T1")

        response = authorized_get(
            self.client, query={"course_key": "course-v1:EPFL+DemoX+2025_T1"}
        )

        self.assertEqual(
            [item["event_id"] for item in response.json()],
            ["epfl"],
        )

    def test_filters_by_instance_name_case_insensitively(self):
        create_event(event_id="epfl", instance_name="epfl")
        create_event(event_id="ethz", instance_name="ethz")

        response = authorized_get(self.client, query={"instance_name": "EPFL"})

        self.assertEqual(
            [item["event_id"] for item in response.json()],
            ["epfl"],
        )

    def test_filters_by_event_type_exactly(self):
        create_event(event_id="published", event_type="course_published")
        create_event(event_id="other", event_type="other_event")

        response = authorized_get(self.client, query={"event_type": "course_published"})

        self.assertEqual(
            [item["event_id"] for item in response.json()],
            ["published"],
        )

    def test_combines_filters(self):
        create_event(
            event_id="match",
            course_key="course-v1:EPFL+DemoX+2025_T1",
            instance_name="epfl",
            event_type="course_published",
        )
        create_event(
            event_id="other-instance",
            course_key="course-v1:EPFL+DemoX+2025_T1",
            instance_name="ethz",
            event_type="course_published",
        )
        create_event(
            event_id="other-type",
            course_key="course-v1:EPFL+DemoX+2025_T1",
            instance_name="epfl",
            event_type="other_event",
        )

        response = authorized_get(
            self.client,
            query={
                "course_key": "course-v1:EPFL+DemoX+2025_T1",
                "instance_name": "EPFL",
                "event_type": "course_published",
            },
        )

        self.assertEqual(
            [item["event_id"] for item in response.json()],
            ["match"],
        )

    def test_ignores_empty_string_filter_values(self):
        create_event(event_id="epfl", instance_name="epfl")

        response = authorized_get(
            self.client,
            query={"course_key": "", "instance_name": "", "event_type": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["event_id"] for item in response.json()], ["epfl"])

    def test_no_matching_events_returns_200_empty_list(self):
        response = authorized_get(
            self.client, query={"course_key": "course-v1:EPFL+Missing+2025_T1"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])


@override_settings(
    SMS_EVENTS_AUTH_TOKEN=AUTH_TOKEN,
    OPENEDX_EVENTS_SERVE_HISTORY=True,
)
class EventsHistoryFlagOnAuthTest(TestCase):
    def test_missing_authorization_header_returns_401(self):
        response = self.client.get(EVENTS_URL)
        self.assertEqual(response.status_code, 401)

    def test_non_bearer_scheme_returns_401(self):
        response = self.client.get(
            EVENTS_URL, HTTP_AUTHORIZATION=f"Basic {AUTH_TOKEN}"
        )
        self.assertEqual(response.status_code, 401)

    def test_wrong_token_returns_403(self):
        response = self.client.get(EVENTS_URL, HTTP_AUTHORIZATION="Bearer wrong-token")
        self.assertEqual(response.status_code, 403)


@override_settings(OPENEDX_EVENTS_SERVE_HISTORY=True)
class EventsHistoryFlagOnWithoutTokenTest(TestCase):
    def test_unset_token_returns_503(self):
        response = self.client.get(EVENTS_URL, HTTP_AUTHORIZATION="Bearer whatever")
        self.assertEqual(response.status_code, 503)
