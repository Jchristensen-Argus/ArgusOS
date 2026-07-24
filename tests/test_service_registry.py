"""Unit tests for argus.services.service_registry.InMemoryServiceRegistry."""

import unittest

from argus.services.exceptions import ServiceNotFoundError, ServiceRegistrationError
from argus.services.service_descriptor import ServiceDescriptor
from argus.services.service_registry import InMemoryServiceRegistry


class FakeInterface:
    pass


class FakeService(FakeInterface):
    def ping(self):
        return "pong"


def _descriptor(name="fake_service", **overrides):
    defaults = dict(
        name=name,
        instance=FakeService(),
        interface=FakeInterface,
        version="1.0.0",
    )
    defaults.update(overrides)
    return ServiceDescriptor(**defaults)


class RegisterTests(unittest.TestCase):
    def test_register_then_contains_is_true(self):
        registry = InMemoryServiceRegistry()
        registry.register(_descriptor())

        self.assertTrue(registry.contains("fake_service"))

    def test_duplicate_registration_raises(self):
        registry = InMemoryServiceRegistry()
        registry.register(_descriptor())

        with self.assertRaises(ServiceRegistrationError):
            registry.register(_descriptor())

    def test_register_rejects_non_descriptor(self):
        registry = InMemoryServiceRegistry()

        with self.assertRaises(ServiceRegistrationError):
            registry.register("not-a-descriptor")

    def test_register_rejects_empty_name(self):
        registry = InMemoryServiceRegistry()

        with self.assertRaises(ServiceRegistrationError):
            registry.register(_descriptor(name=""))

    def test_same_instance_can_register_under_different_names(self):
        registry = InMemoryServiceRegistry()
        service = FakeService()
        registry.register(_descriptor(name="a", instance=service))
        registry.register(_descriptor(name="b", instance=service))

        self.assertTrue(registry.contains("a"))
        self.assertTrue(registry.contains("b"))


class ResolveTests(unittest.TestCase):
    def test_resolve_returns_the_registered_instance(self):
        registry = InMemoryServiceRegistry()
        service = FakeService()
        registry.register(_descriptor(instance=service))

        resolved = registry.resolve("fake_service")

        self.assertIs(resolved, service)
        self.assertEqual(resolved.ping(), "pong")

    def test_resolve_missing_service_raises(self):
        registry = InMemoryServiceRegistry()

        with self.assertRaises(ServiceNotFoundError):
            registry.resolve("missing")

    def test_resolve_after_unregister_raises(self):
        registry = InMemoryServiceRegistry()
        registry.register(_descriptor())
        registry.unregister("fake_service")

        with self.assertRaises(ServiceNotFoundError):
            registry.resolve("fake_service")


class UnregisterTests(unittest.TestCase):
    def test_unregister_removes_the_service(self):
        registry = InMemoryServiceRegistry()
        registry.register(_descriptor())

        registry.unregister("fake_service")

        self.assertFalse(registry.contains("fake_service"))

    def test_unregister_unknown_service_raises(self):
        registry = InMemoryServiceRegistry()

        with self.assertRaises(ServiceNotFoundError):
            registry.unregister("missing")

    def test_unregister_then_reregister_succeeds(self):
        registry = InMemoryServiceRegistry()
        registry.register(_descriptor())
        registry.unregister("fake_service")

        registry.register(_descriptor())

        self.assertTrue(registry.contains("fake_service"))


class ContainsTests(unittest.TestCase):
    def test_contains_false_for_never_registered_service(self):
        registry = InMemoryServiceRegistry()

        self.assertFalse(registry.contains("missing"))


class ListServicesTests(unittest.TestCase):
    def test_list_services_empty_initially(self):
        registry = InMemoryServiceRegistry()

        self.assertEqual(registry.list_services(), ())

    def test_list_services_returns_all_registered_descriptors(self):
        registry = InMemoryServiceRegistry()
        first = _descriptor(name="a")
        second = _descriptor(name="b")
        registry.register(first)
        registry.register(second)

        services = registry.list_services()

        self.assertEqual(len(services), 2)
        self.assertIn(first, services)
        self.assertIn(second, services)

    def test_list_services_preserves_registration_order(self):
        registry = InMemoryServiceRegistry()
        registry.register(_descriptor(name="third"))
        registry.register(_descriptor(name="first"))
        registry.register(_descriptor(name="second"))

        names = [descriptor.name for descriptor in registry.list_services()]

        self.assertEqual(names, ["third", "first", "second"])

    def test_list_services_excludes_unregistered_services(self):
        registry = InMemoryServiceRegistry()
        registry.register(_descriptor(name="a"))
        registry.register(_descriptor(name="b"))
        registry.unregister("a")

        names = [descriptor.name for descriptor in registry.list_services()]

        self.assertEqual(names, ["b"])


if __name__ == "__main__":
    unittest.main()
