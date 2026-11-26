"""The ``events/`` endpoint (ADR 0001, "Webhook contract (binding)")."""

import logging
import secrets
from typing import ClassVar

from django.conf import settings
from django.db import IntegrityError
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from swissmooc_openedx_events.models import EVENT_TYPE_COURSE_PUBLISHED, OpenedxEvent
from swissmooc_openedx_events.serializers import OpenedxEventSerializer

logger = logging.getLogger(__name__)


class SmsEventsAuthMixin:
    """Shared bearer-token auth for sms-events endpoints."""

    authentication_classes: ClassVar[list[type]] = []
    permission_classes: ClassVar[list[type]] = []

    def _authenticate(self, request):
        configured_token = getattr(settings, "SMS_EVENTS_AUTH_TOKEN", "") or ""
        if not configured_token:
            logger.error("SMS_EVENTS_AUTH_TOKEN not configured; rejecting request")
            return Response(
                {"detail": "sms-events is not configured on this app"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header.startswith("Bearer "):
            return Response(
                {"detail": "expected 'Authorization: Bearer <token>'"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token = header[len("Bearer ") :].strip()
        if not secrets.compare_digest(token, configured_token):
            return Response(
                {"detail": "invalid token"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return None


class SmsEventsWebhookMixin(SmsEventsAuthMixin):
    """Shared bearer-token auth and event persistence for webhook endpoints."""

    def post(self, request):
        auth_error = self._authenticate(request)
        if auth_error is not None:
            return auth_error
        return self._handle(request)

    def _handle(self, request):
        raise NotImplementedError

    @staticmethod
    def _bad_request(detail):
        return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)

    def _record_event(self, data):
        """Validate and persist a ``course_published`` envelope.

        A repeated ``event_id`` stores nothing new and answers as if it had
        been stored, with the existing row's ``id`` — including when two
        copies arrive concurrently, which extras' reference leaves as a 500.
        """
        serializer = OpenedxEventSerializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError:
            # Preserve deepseek's 400-with-``detail`` shape instead of DRF's
            # per-field validation error mapping.
            return self._bad_request("invalid event payload")

        validated = serializer.validated_data
        try:
            event, created = OpenedxEvent.objects.get_or_create(
                event_id=validated["event_id"],
                defaults=validated,
            )
        except IntegrityError:
            # Lost a concurrent-insert race on the unique ``event_id``.
            event = OpenedxEvent.objects.get(event_id=validated["event_id"])
            created = False

        if created:
            logger.info(
                "openedx event recorded: %s %s (instance=%s)",
                event.event_type,
                event.course_key,
                event.instance_name,
            )
        else:
            logger.info(
                "openedx event deduped: %s %s (instance=%s, event_id=%s)",
                event.event_type,
                event.course_key,
                event.instance_name,
                event.event_id,
            )

        return Response(
            {
                "status": "accepted",
                "id": event.id,
                "event_id": event.event_id,
                "event_type": event.event_type,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class EventsView(SmsEventsWebhookMixin, APIView):
    """Versioned event-store endpoint used by the openedx-sms-events plugin.

    POST: ingest an event envelope. GET: query event history, opt-in per host
    via ``OPENEDX_EVENTS_SERVE_HISTORY`` (ADR decision 7).
    """

    def _handle(self, request):
        data = request.data
        if not isinstance(data, dict):
            return self._bad_request("body must be a JSON object")

        event_type = data.get("event_type")
        if not isinstance(event_type, str) or not event_type:
            return self._bad_request("event_type is required")

        if event_type == EVENT_TYPE_COURSE_PUBLISHED:
            return self._record_event(data)

        logger.info("unrouted sms-events event_type=%r; accepting as no-op", event_type)
        return Response(
            {"status": "accepted", "event_type": event_type},
            status=status.HTTP_202_ACCEPTED,
        )

    def get(self, request):
        # With history disabled the endpoint answers 404 whatever credentials
        # are presented; the check still precedes this view's explicit auth.
        if not getattr(settings, "OPENEDX_EVENTS_SERVE_HISTORY", False):
            return Response(
                {"detail": "not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        auth_error = self._authenticate(request)
        if auth_error is not None:
            return auth_error

        queryset = OpenedxEvent.objects.order_by("-occurred_at")
        course_key = request.query_params.get("course_key", "")
        instance_name = request.query_params.get("instance_name", "")
        event_type = request.query_params.get("event_type", "")

        if course_key:
            queryset = queryset.filter(course_key=course_key)
        if instance_name:
            queryset = queryset.filter(instance_name__iexact=instance_name)
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        return Response(OpenedxEventSerializer(queryset, many=True).data)
