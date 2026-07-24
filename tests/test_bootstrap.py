"""Unit tests for argus.bootstrap.bootstrap."""

import unittest

from argus.application import Application
from argus.bootstrap import bootstrap
from argus.events import IEventBus, InMemoryEventBus
from argus.knowledge import IKnowledgeService, KnowledgeService
from argus.lifecycle import LifecycleManager, LifecycleState
from argus.services import IServiceRegistry, InMemoryServiceRegistry

CORE_SERVICE_NAMES = (
    "configuration",
    "logger",
    "event_bus",
    "service_registry",
    "lifecycle_manager",
    "knowledge_service",
)


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

    def test_bootstrap_registers_lifecycle_manager_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("lifecycle_manager"))
            lifecycle_manager = application.container.resolve("lifecycle_manager")
            self.assertIsInstance(lifecycle_manager, LifecycleManager)
        finally:
            application.shutdown()

    def test_bootstrap_registers_knowledge_service_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("knowledge_service"))
            knowledge_service = application.container.resolve("knowledge_service")
            self.assertIsInstance(knowledge_service, IKnowledgeService)
            self.assertIsInstance(knowledge_service, KnowledgeService)
        finally:
            application.shutdown()

    def test_bootstrap_registers_core_services_in_service_registry(self):
        application = bootstrap()

        try:
            service_registry = application.container.resolve("service_registry")
            for name in CORE_SERVICE_NAMES:
                self.assertTrue(
                    service_registry.contains(name),
                    msg=f"{name!r} was not registered in the Service Registry",
                )
            self.assertEqual(len(service_registry.list_services()), len(CORE_SERVICE_NAMES))
        finally:
            application.shutdown()

    def test_core_services_report_registered_lifecycle_state(self):
        application = bootstrap()

        try:
            lifecycle_manager = application.container.resolve("lifecycle_manager")
            for name in CORE_SERVICE_NAMES:
                self.assertEqual(
                    lifecycle_manager.status(name),
                    LifecycleState.REGISTERED,
                    msg=f"{name!r} was not LifecycleState.REGISTERED",
                )
        finally:
            application.shutdown()


if __name__ == "__main__":
    unittest.main()
