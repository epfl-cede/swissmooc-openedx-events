"""Tiny URLconf that includes the app the way a host project would."""

from django.urls import include, path

urlpatterns = [
    path("api/v1/", include("swissmooc_openedx_events.urls")),
]
