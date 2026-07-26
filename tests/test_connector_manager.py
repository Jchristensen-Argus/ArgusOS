"""Unit tests for argus.connectors.manager.ConnectorManager."""

import logging
import unittest

from argus.connectors import (
    Connector,
    ConnectorDisabledError,
    ConnectorInvocationError,
    ConnectorManager,
    ConnectorNotFoundError,
    DuplicateConnectorError,
    IConnector,
    IConnectorManager,
    InvalidConnectorError,
    InvalidConnectorStateError,
    MockConnector,
)
from argus.events import EventType, InMemoryEventBus
from argus.lifecycle import LifecycleState


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_connector_manager")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


class _FakeConnector(IConnector):
    """A minimal, fully controllable IConnector stand-in, giving
    tests precise control over connect()/invoke() failures - unlike
    MockConnector, which always succeeds once connected."""

    def __init__(self, *, fail_connect=False, fail_invoke=False):
        self.fail_connect = fail_connect
        self.fail_invoke = fail_invoke
        self.connect_calls = 0
        self.invoke_calls = []
        self._connected = False

    def connect(self):
        self.connect_calls += 1
        if self.fail_connect:
            raise RuntimeError("connect failed")
        self._connected = True

    def disconnect(self):
        self._connected = False

    def invoke(self, operation, *, payload=None):
        self.invoke_calls.append((operation, payload))
        if self.fail_invoke:
            raise RuntimeError("invoke failed")
        return {"echo": operation}

    def health_check(self):
        return self._connected


class ConnectorManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus(logger=_silent_logger())
        self.received = []
        for event_type in (
            EventType.CONNECTOR_REGISTERED,
            EventType.CONNECTOR_ENABLED,
            EventType.CONNECTOR_DISABLED,
            EventType.CONNECTOR_INVOKED,
            EventType.CONNECTOR_FAILED,
        ):
            self.event_bus.subscribe(event_type, self.received.append)
        self.manager = ConnectorManager(event_bus=self.event_bus)

    def _connector(self, **overrides):
        defaults = dict(name="Example", description="d", version="1.0")
        defaults.update(overrides)
        return Connector(**defaults)

    def _running_manager(self):
        self.manager.initialize()
        self.manager.start()
        return self.manager


class ConstructionTests(ConnectorManagerTestCase):
    def test_implements_iconnector_manager(self):
        self.assertIsInstance(self.manager, IConnectorManager)

    def test_starts_in_created_state(self):
        self.assertEqual(self.manager.status(), LifecycleState.CREATED)

    def test_starts_with_no_connectors(self):
        self.assertEqual(self.manager.list_connectors(), ())


class RegistrationTests(ConnectorManagerTestCase):
    def test_register_then_get(self):
        connector = self._connector()

        self.manager.register_connector(connector, MockConnector())

        self.assertEqual(self.manager.get_connector(connector.id), connector)

    def test_register_publishes_connector_registered(self):
        connector = self._connector()

        self.manager.register_connector(connector, MockConnector())

        types = [event.type for event in self.received]
        self.assertIn(EventType.CONNECTOR_REGISTERED, types)

    def test_register_rejects_non_connector(self):
        with self.assertRaises(InvalidConnectorError):
            self.manager.register_connector("not-a-connector", MockConnector())

    def test_register_rejects_empty_name(self):
        connector = Connector(name="", description="d", version="1.0")

        with self.assertRaises(InvalidConnectorError):
            self.manager.register_connector(connector, MockConnector())

    def test_register_rejects_empty_version(self):
        connector = Connector(name="Example", description="d", version="")

        with self.assertRaises(InvalidConnectorError):
            self.manager.register_connector(connector, MockConnector())

    def test_register_rejects_missing_implementation(self):
        connector = self._connector()

        with self.assertRaises(InvalidConnectorError):
            self.manager.register_connector(connector, None)

    def test_register_rejects_empty_id(self):
        connector = Connector(id="", name="Example", description="d", version="1.0")

        with self.assertRaises(InvalidConnectorError):
            self.manager.register_connector(connector, MockConnector())

    def test_duplicate_registration_raises(self):
        connector = self._connector()
        self.manager.register_connector(connector, MockConnector())

        with self.assertRaises(DuplicateConnectorError):
            self.manager.register_connector(connector, MockConnector())

    def test_duplicate_registration_does_not_publish_again(self):
        connector = self._connector()
        self.manager.register_connector(connector, MockConnector())
        self.received.clear()

        with self.assertRaises(DuplicateConnectorError):
            self.manager.register_connector(connector, MockConnector())

        self.assertEqual(self.received, [])


class LookupTests(ConnectorManagerTestCase):
    def test_get_unknown_connector_raises(self):
        with self.assertRaises(ConnectorNotFoundError):
            self.manager.get_connector("unknown")

    def test_get_with_empty_id_raises_invalid_connector_error(self):
        with self.assertRaises(InvalidConnectorError):
            self.manager.get_connector("")

    def test_get_with_non_string_id_raises_invalid_connector_error(self):
        with self.assertRaises(InvalidConnectorError):
            self.manager.get_connector(123)

    def test_list_connectors_returns_all_registered(self):
        first = self._connector(name="First")
        second = self._connector(name="Second")
        self.manager.register_connector(first, MockConnector())
        self.manager.register_connector(second, MockConnector())

        listed = self.manager.list_connectors()

        self.assertEqual(len(listed), 2)
        self.assertIn(first, listed)
        self.assertIn(second, listed)


class UnregisterTests(ConnectorManagerTestCase):
    def test_unregister_removes_connector(self):
        connector = self._connector()
        self.manager.register_connector(connector, MockConnector())

        self.manager.unregister_connector(connector.id)

        with self.assertRaises(ConnectorNotFoundError):
            self.manager.get_connector(connector.id)

    def test_unregister_unknown_connector_raises(self):
        with self.assertRaises(ConnectorNotFoundError):
            self.manager.unregister_connector("unknown")

    def test_unregister_publishes_nothing(self):
        connector = self._connector()
        self.manager.register_connector(connector, MockConnector())
        self.received.clear()

        self.manager.unregister_connector(connector.id)

        self.assertEqual(self.received, [])

    def test_unregistered_connector_can_no_longer_be_invoked(self):
        connector = self._connector()
        self.manager.register_connector(connector, MockConnector())
        self.manager.unregister_connector(connector.id)
        self._running_manager()

        with self.assertRaises(ConnectorNotFoundError):
            self.manager.invoke(connector.id, "op")


class EnableDisableTests(ConnectorManagerTestCase):
    def test_disable_sets_enabled_false(self):
        connector = self._connector()
        self.manager.register_connector(connector, MockConnector())

        updated = self.manager.disable_connector(connector.id)

        self.assertFalse(updated.enabled)
        self.assertFalse(self.manager.get_connector(connector.id).enabled)

    def test_disable_publishes_connector_disabled(self):
        connector = self._connector()
        self.manager.register_connector(connector, MockConnector())
        self.received.clear()

        self.manager.disable_connector(connector.id)

        types = [event.type for event in self.received]
        self.assertIn(EventType.CONNECTOR_DISABLED, types)

    def test_enable_sets_enabled_true(self):
        connector = self._connector()
        self.manager.register_connector(connector, MockConnector())
        self.manager.disable_connector(connector.id)

        updated = self.manager.enable_connector(connector.id)

        self.assertTrue(updated.enabled)

    def test_enable_publishes_connector_enabled_even_if_already_enabled(self):
        connector = self._connector()
        self.manager.register_connector(connector, MockConnector())
        self.received.clear()

        self.manager.enable_connector(connector.id)

        types = [event.type for event in self.received]
        self.assertIn(EventType.CONNECTOR_ENABLED, types)

    def test_disable_unknown_connector_raises(self):
        with self.assertRaises(ConnectorNotFoundError):
            self.manager.disable_connector("unknown")

    def test_enable_unknown_connector_raises(self):
        with self.assertRaises(ConnectorNotFoundError):
            self.manager.enable_connector("unknown")


class InvokeStateGateTests(ConnectorManagerTestCase):
    def test_invoke_before_running_raises(self):
        connector = self._connector()
        self.manager.register_connector(connector, MockConnector())

        with self.assertRaises(InvalidConnectorStateError):
            self.manager.invoke(connector.id, "op")

    def test_invoke_after_stop_raises(self):
        connector = self._connector()
        self.manager.register_connector(connector, MockConnector())
        self._running_manager()
        self.manager.stop()

        with self.assertRaises(InvalidConnectorStateError):
            self.manager.invoke(connector.id, "op")


class InvokeTests(ConnectorManagerTestCase):
    def test_invoke_returns_implementation_result(self):
        connector = self._connector()
        self.manager.register_connector(connector, MockConnector())
        self._running_manager()

        result = self.manager.invoke(connector.id, "op", payload={"a": 1})

        self.assertEqual(result["operation"], "op")
        self.assertEqual(result["payload"], {"a": 1})

    def test_invoke_calls_connect_before_invoke(self):
        connector = self._connector()
        implementation = _FakeConnector()
        self.manager.register_connector(connector, implementation)
        self._running_manager()

        self.manager.invoke(connector.id, "op")

        self.assertEqual(implementation.connect_calls, 1)
        self.assertEqual(implementation.invoke_calls, [("op", None)])

    def test_invoke_is_idempotent_with_respect_to_connect(self):
        connector = self._connector()
        implementation = _FakeConnector()
        self.manager.register_connector(connector, implementation)
        self._running_manager()

        self.manager.invoke(connector.id, "op")
        self.manager.invoke(connector.id, "op")

        self.assertEqual(implementation.connect_calls, 2)
        self.assertTrue(implementation.health_check())

    def test_invoke_publishes_connector_invoked(self):
        connector = self._connector()
        self.manager.register_connector(connector, MockConnector())
        self._running_manager()
        self.received.clear()

        self.manager.invoke(connector.id, "op")

        types = [event.type for event in self.received]
        self.assertIn(EventType.CONNECTOR_INVOKED, types)

    def test_invoke_unknown_connector_raises(self):
        self._running_manager()

        with self.assertRaises(ConnectorNotFoundError):
            self.manager.invoke("unknown", "op")

    def test_invoke_disabled_connector_raises(self):
        connector = self._connector()
        self.manager.register_connector(connector, MockConnector())
        self.manager.disable_connector(connector.id)
        self._running_manager()

        with self.assertRaises(ConnectorDisabledError):
            self.manager.invoke(connector.id, "op")

    def test_invoke_empty_operation_raises(self):
        connector = self._connector()
        self.manager.register_connector(connector, MockConnector())
        self._running_manager()

        with self.assertRaises(InvalidConnectorError):
            self.manager.invoke(connector.id, "")

    def test_invoke_wraps_connect_failure(self):
        connector = self._connector()
        implementation = _FakeConnector(fail_connect=True)
        self.manager.register_connector(connector, implementation)
        self._running_manager()

        with self.assertRaises(ConnectorInvocationError):
            self.manager.invoke(connector.id, "op")

    def test_invoke_wraps_invoke_failure(self):
        connector = self._connector()
        implementation = _FakeConnector(fail_invoke=True)
        self.manager.register_connector(connector, implementation)
        self._running_manager()

        with self.assertRaises(ConnectorInvocationError):
            self.manager.invoke(connector.id, "op")

    def test_failed_invoke_publishes_connector_failed_not_invoked(self):
        connector = self._connector()
        implementation = _FakeConnector(fail_invoke=True)
        self.manager.register_connector(connector, implementation)
        self._running_manager()
        self.received.clear()

        with self.assertRaises(ConnectorInvocationError):
            self.manager.invoke(connector.id, "op")

        types = [event.type for event in self.received]
        self.assertIn(EventType.CONNECTOR_FAILED, types)
        self.assertNotIn(EventType.CONNECTOR_INVOKED, types)


class HealthCheckThroughImplementationTests(ConnectorManagerTestCase):
    def test_health_check_reflects_connection_state_after_invoke(self):
        connector = self._connector()
        implementation = MockConnector()
        self.manager.register_connector(connector, implementation)
        self._running_manager()

        self.assertFalse(implementation.health_check())
        self.manager.invoke(connector.id, "op")
        self.assertTrue(implementation.health_check())


class LifecycleTests(ConnectorManagerTestCase):
    def test_initialize_then_start_transitions_to_running(self):
        self.manager.initialize()
        self.manager.start()

        self.assertEqual(self.manager.status(), LifecycleState.RUNNING)

    def test_stop_transitions_to_stopped(self):
        self.manager.initialize()
        self.manager.start()
        self.manager.stop()

        self.assertEqual(self.manager.status(), LifecycleState.STOPPED)

    def test_start_before_initialize_raises(self):
        with self.assertRaises(Exception):
            self.manager.start()

    def test_stop_before_start_raises(self):
        self.manager.initialize()

        with self.assertRaises(Exception):
            self.manager.stop()

    def test_initialize_twice_raises(self):
        self.manager.initialize()

        with self.assertRaises(Exception):
            self.manager.initialize()


if __name__ == "__main__":
    unittest.main()
