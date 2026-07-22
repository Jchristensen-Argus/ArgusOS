"""Unit tests for argus.bootstrap.bootstrap."""

import unittest

from argus.application import Application
from argus.bootstrap import bootstrap


class BootstrapTests(unittest.TestCase):
    def test_bootstrap_returns_running_application(self):
        application = bootstrap()

        try:
            self.assertIsInstance(application, Application)
            self.assertTrue(application.is_running)
            self.assertTrue(application.container.has("configuration"))
            self.assertTrue(application.container.has("logger"))
        finally:
            application.shutdown()

    def test_bootstrap_application_shuts_down_cleanly(self):
        application = bootstrap()

        application.shutdown()

        self.assertFalse(application.is_running)


if __name__ == "__main__":
    unittest.main()
