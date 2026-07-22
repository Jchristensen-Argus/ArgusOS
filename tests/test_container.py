"""Unit tests for argus.container.Container."""

import unittest

from argus.container import (
    Container,
    ServiceAlreadyRegisteredError,
    ServiceNotRegisteredError,
)


class ContainerTests(unittest.TestCase):
    def test_register_and_resolve_returns_same_instance(self):
        container = Container()
        service = object()

        container.register("thing", service)

        self.assertIs(container.resolve("thing"), service)

    def test_resolve_unknown_service_raises(self):
        container = Container()

        with self.assertRaises(ServiceNotRegisteredError):
            container.resolve("missing")

    def test_register_duplicate_name_raises(self):
        container = Container()
        container.register("thing", object())

        with self.assertRaises(ServiceAlreadyRegisteredError):
            container.register("thing", object())

    def test_has_reflects_registration_state(self):
        container = Container()

        self.assertFalse(container.has("thing"))

        container.register("thing", object())

        self.assertTrue(container.has("thing"))


if __name__ == "__main__":
    unittest.main()
