"""URL patterns for the swissmooc_openedx_events app.

Host projects include this URLconf with:

    path("api/v1/", include("swissmooc_openedx_events.urls"))

Endpoints are added in later tickets.
"""

from django.urls import path

from swissmooc_openedx_events.views import EventsView

app_name = "swissmooc_openedx_events"

urlpatterns = [
    path("events/", EventsView.as_view(), name="events"),
]
