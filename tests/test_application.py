"""Unit tests for argus.application.Application."""

import unittest

from argus.application import Application
from argus.container import Container
from argus.logging_service import get_logger


def _container_with_logger() -> Container:
    container = Container()
    container.register("logger", get_logger("test"))
    return container


class ApplicationTests(unittest.TestCase):
    def test_application_starts_and_reports_running(self):
        application = Application(_container_with_logger())

        self.assertFalse(application.is_running)

        application.start()

        self.assertTrue(application.is_running)

    def test_application_shutdown_reports_not_running(self):
        application = Application(_container_with_logger())
        application.start()

        application.shutdown()

        self.assertFalse(application.is_running)

    def test_application_shutdown_is_safe_without_start(self):
        application = Application(_container_with_logger())

        application.shutdown()

        self.assertFalse(application.is_running)

    def test_application_exposes_its_container(self):
        container = _container_with_logger()
        application = Application(container)

        self.assertIs(application.container, container)


if __name__ == "__main__":
    unittest.main()
