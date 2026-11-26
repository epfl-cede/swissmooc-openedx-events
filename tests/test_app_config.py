from django.apps import apps
from django.test import SimpleTestCase

import swissmooc_openedx_events


class AppConfigSmokeTest(SimpleTestCase):
    def test_app_config_installs_with_expected_label(self):
        assert swissmooc_openedx_events.__name__ == "swissmooc_openedx_events"
        app_config = apps.get_app_config("swissmooc_openedx_events")
        assert app_config.label == "swissmooc_openedx_events"
