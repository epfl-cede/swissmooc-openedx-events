from django.db import models

EVENT_TYPE_COURSE_PUBLISHED = "course_published"


class OpenedxEventManager(models.Manager):
    def course_published_for_organisation(self, instance_name):
        """Return all ``course_published`` events for an organisation."""
        return self.filter(
            event_type=EVENT_TYPE_COURSE_PUBLISHED,
            instance_name__iexact=instance_name,
        )

    def latest_course_publish(self, course_key, instance_name):
        """Return the latest ``course_published`` event for a course/instance."""
        return (
            self.course_published_for_organisation(instance_name)
            .filter(course_key=course_key)
            .order_by("-occurred_at")
            .first()
        )


class OpenedxEvent(models.Model):
    """A generic Open edX event received from the openedx-sms-events plugin.

    The plugin stamps every payload with a stable ``event_id`` (a one-time
    UUID) and an ``occurred_at`` timestamp. ``event_id`` is the deduplication
    key: a retried event yields one row. Distinct publishes produce distinct
    rows, so this table is a durable event history consumers can pull.

    ``course_xml_dump`` reads the latest ``course_published`` row for each
    course directly from this table to decide whether a fresh XML dump is
    needed.
    """

    event_id = models.CharField(max_length=64, unique=True)
    event_type = models.CharField(max_length=64, db_index=True)
    course_key = models.CharField(max_length=255, db_index=True)
    org = models.CharField(max_length=255)
    course = models.CharField(max_length=255)
    run = models.CharField(max_length=255)
    instance_name = models.CharField(max_length=64, db_index=True)
    occurred_at = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = OpenedxEventManager()

    def __str__(self):
        return f"{self.event_type} {self.course_key} ({self.instance_name})"

    class Meta:
        ordering = ("-occurred_at",)
        get_latest_by = "occurred_at"
        indexes = (
            models.Index(fields=["course_key", "instance_name", "-occurred_at"]),
        )
