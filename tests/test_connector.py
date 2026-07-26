"""Unit tests for argus.connectors.connector.Connector and
argus.connectors.manager.MockConnector."""

import unittest
from types import MappingProxyType

from argus.connectors import Connector, ConnectorInvocationError, MockConnector


class ConnectorTests(unittest.TestCase):
    def test_defaults(self):
        connector = Connector(name="Example", description="d", version="1.0")

        self.assertTrue(connector.id)
        self.assertTrue(connector.enabled)
        self.assertEqual(connector.capabilities, ())
        self.assertEqual(dict(connector.metadata), {})

    def test_ids_are_unique(self):
        first = Connector(name="A", description="d", version="1.0")
        second = Connector(name="B", description="d", version="1.0")

        self.assertNotEqual(first.id, second.id)

    def test_capabilities_are_coerced_to_a_tuple(self):
        connector = Connector(
            name="Example", description="d", version="1.0", capabilities=["a", "b"]
        )

        self.assertEqual(connector.capabilities, ("a", "b"))
        self.assertIsInstance(connector.capabilities, tuple)

    def test_metadata_is_an_immutable_mapping(self):
        connector = Connector(
            name="Example", description="d", version="1.0", metadata={"k": "v"}
        )

        self.assertIsInstance(connector.metadata, MappingProxyType)
        with self.assertRaises(TypeError):
            connector.metadata["k"] = "other"

    def test_is_frozen(self):
        connector = Connector(name="Example", description="d", version="1.0")

        with self.assertRaises(Exception):
            connector.name = "Changed"

    def test_explicit_id_is_preserved(self):
        connector = Connector(
            id="custom-id", name="Example", description="d", version="1.0"
        )

        self.assertEqual(connector.id, "custom-id")


class MockConnectorTests(unittest.TestCase):
    def test_starts_disconnected(self):
        connector = MockConnector()

        self.assertFalse(connector.health_check())

    def test_connect_then_health_check_reports_true(self):
        connector = MockConnector()

        connector.connect()

        self.assertTrue(connector.health_check())

    def test_connect_is_idempotent(self):
        connector = MockConnector()

        connector.connect()
        connector.connect()

        self.assertTrue(connector.health_check())

    def test_disconnect_then_health_check_reports_false(self):
        connector = MockConnector()

        connector.connect()
        connector.disconnect()

        self.assertFalse(connector.health_check())

    def test_disconnect_is_idempotent(self):
        connector = MockConnector()

        connector.disconnect()
        connector.disconnect()

        self.assertFalse(connector.health_check())

    def test_invoke_without_connect_raises(self):
        connector = MockConnector()

        with self.assertRaises(ConnectorInvocationError):
            connector.invoke("op")

    def test_invoke_after_connect_returns_operation_and_payload(self):
        connector = MockConnector()
        connector.connect()

        result = connector.invoke("do_thing", payload={"x": 1})

        self.assertEqual(result["operation"], "do_thing")
        self.assertEqual(result["payload"], {"x": 1})

    def test_invoke_with_no_payload_defaults_to_empty_dict(self):
        connector = MockConnector()
        connector.connect()

        result = connector.invoke("do_thing")

        self.assertEqual(result["payload"], {})

    def test_custom_response_is_merged_into_result(self):
        connector = MockConnector(response={"status": "ok", "code": 200})
        connector.connect()

        result = connector.invoke("do_thing")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["code"], 200)
        self.assertEqual(result["operation"], "do_thing")

    def test_invoke_after_disconnect_raises_again(self):
        connector = MockConnector()
        connector.connect()
        connector.invoke("op")
        connector.disconnect()

        with self.assertRaises(ConnectorInvocationError):
            connector.invoke("op")


if __name__ == "__main__":
    unittest.main()
