"""Django settings for the test project."""

SECRET_KEY = "test-secret-key"

INSTALLED_APPS = [
    # DRF's APIView imports permissions backed by these built-in apps.
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "swissmooc_openedx_events",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

ROOT_URLCONF = "tests.urls"

USE_TZ = True
