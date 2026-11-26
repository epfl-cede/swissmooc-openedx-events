"""Validate and expose Open edX events.

Modeled after swissmooc-extras' ``apps.openedx_events.serializers`` and used
for both POST payload validation and GET history representation.
"""
from rest_framework import serializers

from swissmooc_openedx_events.models import OpenedxEvent


class OpenedxEventSerializer(serializers.ModelSerializer):
    """Validate a webhook envelope into an ``OpenedxEvent`` row.

    Field lengths come from the model; the serializer enforces them because
    SQLite never does. Fields are declared explicitly, as in extras, with the
    model's max lengths propagated by hand (explicit declarations bypass
    ``build_standard_field``, which would otherwise infer them from the
    model).
    """

    event_id = serializers.CharField(required=True, allow_blank=False, max_length=64)
    event_type = serializers.CharField(required=True, allow_blank=False, max_length=64)
    occurred_at = serializers.DateTimeField(required=True)
    course_key = serializers.CharField(required=True, allow_blank=False, max_length=255)

    org = serializers.CharField(required=True, allow_blank=False, max_length=255)
    course = serializers.CharField(required=True, allow_blank=False, max_length=255)
    run = serializers.CharField(required=True, allow_blank=False, max_length=255)
    instance_name = serializers.CharField(required=True, allow_blank=False, max_length=64)

    class Meta:
        model = OpenedxEvent
        fields = (
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
        )
        read_only_fields = ("id", "received_at")
