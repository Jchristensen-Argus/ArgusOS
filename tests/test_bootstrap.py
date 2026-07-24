"""Unit tests for argus.bootstrap.bootstrap."""

import unittest

from argus.application import Application
from argus.bootstrap import bootstrap
from argus.events import IEventBus, InMemoryEventBus
from argus.services import IServiceRegistry, InMemoryServiceRegistry


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

    def test_bootstrap_registers_event_bus_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("event_bus"))
            event_bus = application.container.resolve("event_bus")
            self.assertIsInstance(event_bus, IEventBus)
            self.assertIsInstance(event_bus, InMemoryEventBus)
        finally:
            application.shutdown()

    def test_bootstrap_registers_service_registry_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("service_registry"))
            service_registry = application.container.resolve("service_registry")
            self.assertIsInstance(service_registry, IServiceRegistry)
            self.assertIsInstance(service_registry, InMemoryServiceRegistry)
        finally:
            application.shutdown()


if __name__ == "__main__":
    unittest.main()
