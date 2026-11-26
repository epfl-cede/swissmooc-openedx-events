from django.contrib import admin

from swissmooc_openedx_events.models import OpenedxEvent


class OpenedxEventAdmin(admin.ModelAdmin):
    list_display = (
        "event_type",
        "course_key",
        "instance_name",
        "event_id",
        "occurred_at",
        "received_at",
    )
    search_fields = (
        "course_key",
        "org",
        "course",
        "run",
        "instance_name",
        "event_id",
    )
    list_filter = ("event_type", "instance_name", "received_at")
    readonly_fields = (
        "event_id",
        "event_type",
        "occurred_at",
        "received_at",
        "course_key",
        "org",
        "course",
        "run",
        "instance_name",
    )


admin.site.register(OpenedxEvent, OpenedxEventAdmin)
