"""Unit tests for argus.plugins.manager.PluginManager."""

import logging
import unittest

from argus.capability import Capability
from argus.events import EventType, InMemoryEventBus
from argus.intent import IntentType
from argus.plugins import (
    DuplicatePluginError,
    InvalidPluginError,
    IPluginManager,
    Plugin,
    PluginManager,
    PluginNotFoundError,
)


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_plugin_manager")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


def _capability(**overrides):
    defaults = dict(
        name="Answer",
        description="Answers questions.",
        intent_types=[IntentType.QUESTION],
        action_kind="workflow",
        workflow_id="answer_workflow",
    )
    defaults.update(overrides)
    return Capability(**defaults)


def _plugin(**overrides):
    defaults = dict(
        name="Core Workflows",
        version="1.0.0",
        author="ArgusOS",
        description="A test plugin.",
    )
    defaults.update(overrides)
    return Plugin(**defaults)


class ManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus(logger=_silent_logger())
        self.manager = PluginManager(event_bus=self.event_bus)
        self.received = []
        for event_type in EventType:
            self.event_bus.subscribe(event_type, self.received.append)


# -- interface / not-an-IService ------------------------------------------


class PluginManagerIdentityTests(unittest.TestCase):
    def test_is_an_ipluginmanager(self):
        manager = PluginManager(event_bus=InMemoryEventBus(logger=_silent_logger()))
        self.assertIsInstance(manager, IPluginManager)

    def test_is_not_an_iservice(self):
        # Deliberate: PluginManager does not adopt IService - see
        # argus/plugins/interfaces.py's Architectural Note.
        from argus.lifecycle import IService

        manager = PluginManager(event_bus=InMemoryEventBus(logger=_silent_logger()))
        self.assertNotIsInstance(manager, IService)

    def test_all_manager_methods_available_immediately(self):
        # No lifecycle to initialize/start - every method works the
        # instant the manager is constructed.
        manager = PluginManager(event_bus=InMemoryEventBus(logger=_silent_logger()))
        manager.register(_plugin())  # must not raise
        self.assertTrue(manager.contains(manager.list_plugins()[0].id))


# -- register() -------------------------------------------------------------


class RegisterTests(ManagerTestCase):
    def test_register_makes_plugin_discoverable(self):
        plugin = _plugin()

        self.manager.register(plugin)

        self.assertTrue(self.manager.contains(plugin.id))
        self.assertIs(self.manager.get(plugin.id), plugin)

    def test_register_rejects_non_plugin(self):
        with self.assertRaises(InvalidPluginError):
            self.manager.register(object())

    def test_register_rejects_empty_id(self):
        with self.assertRaises(InvalidPluginError):
            self.manager.register(_plugin(id=""))

    def test_register_rejects_empty_name(self):
        with self.assertRaises(InvalidPluginError):
            self.manager.register(_plugin(name=""))

    def test_register_rejects_empty_version(self):
        with self.assertRaises(InvalidPluginError):
            self.manager.register(_plugin(version=""))

    def test_register_rejects_empty_author(self):
        with self.assertRaises(InvalidPluginError):
            self.manager.register(_plugin(author=""))

    def test_register_rejects_non_capability_export(self):
        with self.assertRaises(InvalidPluginError):
            self.manager.register(_plugin(exported_capabilities=["not-a-capability"]))

    def test_register_allows_empty_exported_capabilities(self):
        self.manager.register(_plugin(exported_capabilities=[]))  # must not raise

    def test_register_allows_valid_exported_capabilities(self):
        capability = _capability()
        self.manager.register(_plugin(exported_capabilities=[capability]))  # must not raise

    def test_duplicate_id_raises(self):
        plugin = _plugin(id="dup-id")
        self.manager.register(plugin)

        with self.assertRaises(DuplicatePluginError):
            self.manager.register(_plugin(id="dup-id"))

    def test_register_after_unregister_succeeds(self):
        plugin = _plugin(id="reused-id")
        self.manager.register(plugin)
        self.manager.unregister(plugin.id)

        self.manager.register(_plugin(id="reused-id"))  # must not raise

    def test_register_publishes_plugin_registered(self):
        plugin = _plugin()

        self.manager.register(plugin)

        events = [e for e in self.received if e.type == EventType.PLUGIN_REGISTERED]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["plugin_id"], plugin.id)
        self.assertEqual(events[0].payload["name"], plugin.name)

    def test_failed_register_does_not_publish(self):
        with self.assertRaises(InvalidPluginError):
            self.manager.register(_plugin(name=""))

        self.assertEqual(self.received, [])


# -- unregister() -------------------------------------------------------------


class UnregisterTests(ManagerTestCase):
    def test_unregister_removes_plugin(self):
        plugin = _plugin()
        self.manager.register(plugin)

        self.manager.unregister(plugin.id)

        self.assertFalse(self.manager.contains(plugin.id))

    def test_unregister_rejects_non_string(self):
        with self.assertRaises(InvalidPluginError):
            self.manager.unregister(123)

    def test_unregister_unknown_id_raises(self):
        with self.assertRaises(PluginNotFoundError):
            self.manager.unregister("missing")

    def test_unregister_publishes_plugin_unregistered(self):
        plugin = _plugin()
        self.manager.register(plugin)
        self.received.clear()

        self.manager.unregister(plugin.id)

        events = [e for e in self.received if e.type == EventType.PLUGIN_UNREGISTERED]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["plugin_id"], plugin.id)

    def test_failed_unregister_does_not_publish(self):
        with self.assertRaises(PluginNotFoundError):
            self.manager.unregister("missing")

        self.assertEqual(self.received, [])


# -- enable() / disable() ----------------------------------------------------


class EnableDisableTests(ManagerTestCase):
    def test_disable_sets_enabled_false(self):
        plugin = _plugin()
        self.manager.register(plugin)

        self.manager.disable(plugin.id)

        self.assertFalse(self.manager.get(plugin.id).enabled)

    def test_enable_sets_enabled_true(self):
        plugin = _plugin(enabled=False)
        self.manager.register(plugin)

        self.manager.enable(plugin.id)

        self.assertTrue(self.manager.get(plugin.id).enabled)

    def test_enable_preserves_other_fields(self):
        capability = _capability()
        plugin = _plugin(enabled=False, exported_capabilities=[capability])
        self.manager.register(plugin)

        self.manager.enable(plugin.id)

        updated = self.manager.get(plugin.id)
        self.assertEqual(updated.id, plugin.id)
        self.assertEqual(updated.name, plugin.name)
        self.assertEqual(updated.exported_capabilities, (capability,))

    def test_enable_already_enabled_plugin_is_safe(self):
        plugin = _plugin(enabled=True)
        self.manager.register(plugin)

        self.manager.enable(plugin.id)  # must not raise

        self.assertTrue(self.manager.get(plugin.id).enabled)

    def test_disable_already_disabled_plugin_is_safe(self):
        plugin = _plugin(enabled=False)
        self.manager.register(plugin)

        self.manager.disable(plugin.id)  # must not raise

        self.assertFalse(self.manager.get(plugin.id).enabled)

    def test_enable_rejects_non_string(self):
        with self.assertRaises(InvalidPluginError):
            self.manager.enable(123)

    def test_disable_rejects_non_string(self):
        with self.assertRaises(InvalidPluginError):
            self.manager.disable(123)

    def test_enable_unknown_id_raises(self):
        with self.assertRaises(PluginNotFoundError):
            self.manager.enable("missing")

    def test_disable_unknown_id_raises(self):
        with self.assertRaises(PluginNotFoundError):
            self.manager.disable("missing")

    def test_enable_publishes_plugin_enabled(self):
        plugin = _plugin(enabled=False)
        self.manager.register(plugin)
        self.received.clear()

        self.manager.enable(plugin.id)

        events = [e for e in self.received if e.type == EventType.PLUGIN_ENABLED]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["plugin_id"], plugin.id)

    def test_disable_publishes_plugin_disabled(self):
        plugin = _plugin(enabled=True)
        self.manager.register(plugin)
        self.received.clear()

        self.manager.disable(plugin.id)

        events = [e for e in self.received if e.type == EventType.PLUGIN_DISABLED]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["plugin_id"], plugin.id)

    def test_failed_enable_does_not_publish(self):
        with self.assertRaises(PluginNotFoundError):
            self.manager.enable("missing")

        self.assertEqual(self.received, [])

    def test_failed_disable_does_not_publish(self):
        with self.assertRaises(PluginNotFoundError):
            self.manager.disable("missing")

        self.assertEqual(self.received, [])


# -- get() -------------------------------------------------------------


class GetTests(ManagerTestCase):
    def test_get_returns_registered_plugin(self):
        plugin = _plugin()
        self.manager.register(plugin)

        self.assertIs(self.manager.get(plugin.id), plugin)

    def test_get_rejects_non_string(self):
        with self.assertRaises(InvalidPluginError):
            self.manager.get(123)

    def test_get_unknown_id_raises(self):
        with self.assertRaises(PluginNotFoundError):
            self.manager.get("missing")


# -- list_plugins() -------------------------------------------------------------


class ListPluginsTests(ManagerTestCase):
    def test_empty_by_default(self):
        self.assertEqual(self.manager.list_plugins(), ())

    def test_returns_all_registered_plugins_in_registration_order(self):
        first = _plugin(id="first")
        second = _plugin(id="second", name="Second")
        self.manager.register(first)
        self.manager.register(second)

        self.assertEqual(self.manager.list_plugins(), (first, second))

    def test_includes_disabled_plugins(self):
        # list_plugins() is a pure enumeration - it applies no
        # enabled/disabled policy. See IPluginManager's docstring.
        plugin = _plugin(enabled=False)
        self.manager.register(plugin)

        self.assertIn(plugin, self.manager.list_plugins())

    def test_does_not_publish_events(self):
        self.manager.register(_plugin())
        self.received.clear()

        self.manager.list_plugins()

        self.assertEqual(self.received, [])


# -- list_exported_capabilities() --------------------------------------------


class ListExportedCapabilitiesTests(ManagerTestCase):
    def test_empty_by_default(self):
        self.assertEqual(self.manager.list_exported_capabilities(), ())

    def test_returns_capabilities_from_single_plugin(self):
        cap_a = _capability(name="A")
        cap_b = _capability(name="B", intent_types=[IntentType.COMMAND])
        self.manager.register(_plugin(exported_capabilities=[cap_a, cap_b]))

        self.assertEqual(self.manager.list_exported_capabilities(), (cap_a, cap_b))

    def test_aggregates_across_plugins_in_registration_order(self):
        cap_a = _capability(name="A")
        cap_b = _capability(name="B", intent_types=[IntentType.COMMAND])
        self.manager.register(_plugin(id="first", exported_capabilities=[cap_a]))
        self.manager.register(_plugin(id="second", name="Second", exported_capabilities=[cap_b]))

        self.assertEqual(self.manager.list_exported_capabilities(), (cap_a, cap_b))

    def test_includes_capabilities_from_disabled_plugins(self):
        # A pure aggregation - applies no enabled/disabled policy on
        # either the Plugin or the Capability. See IPluginManager's
        # docstring.
        capability = _capability()
        self.manager.register(_plugin(enabled=False, exported_capabilities=[capability]))

        self.assertIn(capability, self.manager.list_exported_capabilities())

    def test_plugin_with_no_exports_contributes_nothing(self):
        self.manager.register(_plugin(exported_capabilities=[]))

        self.assertEqual(self.manager.list_exported_capabilities(), ())

    def test_does_not_publish_events(self):
        self.manager.register(_plugin(exported_capabilities=[_capability()]))
        self.received.clear()

        self.manager.list_exported_capabilities()

        self.assertEqual(self.received, [])


# -- contains() -------------------------------------------------------------


class ContainsTests(ManagerTestCase):
    def test_true_for_registered_plugin(self):
        plugin = _plugin()
        self.manager.register(plugin)

        self.assertTrue(self.manager.contains(plugin.id))

    def test_false_for_unregistered_plugin(self):
        self.assertFalse(self.manager.contains("missing"))

    def test_never_raises_for_non_string(self):
        self.assertFalse(self.manager.contains(123))
        self.assertFalse(self.manager.contains(None))
        self.assertFalse(self.manager.contains(object()))


if __name__ == "__main__":
    unittest.main()
