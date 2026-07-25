"""Unit tests for argus.plugins.plugin.Plugin."""

import unittest
from types import MappingProxyType

from argus.capability import Capability
from argus.intent import IntentType
from argus.plugins import Plugin


def _capability(**overrides):
    defaults = dict(
        name="Answer",
        description="d",
        intent_types=[IntentType.QUESTION],
        action_kind="workflow",
        workflow_id="answer_workflow",
    )
    defaults.update(overrides)
    return Capability(**defaults)


class PluginConstructionTests(unittest.TestCase):
    def test_minimal_construction(self):
        plugin = Plugin(name="Core", version="1.0.0", author="ArgusOS", description="d")

        self.assertEqual(plugin.name, "Core")
        self.assertEqual(plugin.version, "1.0.0")
        self.assertEqual(plugin.author, "ArgusOS")
        self.assertEqual(plugin.description, "d")

    def test_id_auto_generated_and_unique(self):
        a = Plugin(name="A", version="1.0", author="x", description="d")
        b = Plugin(name="B", version="1.0", author="x", description="d")

        self.assertTrue(a.id)
        self.assertNotEqual(a.id, b.id)

    def test_explicit_id_honored(self):
        plugin = Plugin(name="Core", version="1.0", author="x", description="d", id="fixed-id")

        self.assertEqual(plugin.id, "fixed-id")

    def test_enabled_defaults_to_true(self):
        plugin = Plugin(name="Core", version="1.0", author="x", description="d")

        self.assertTrue(plugin.enabled)

    def test_enabled_honored(self):
        plugin = Plugin(name="Core", version="1.0", author="x", description="d", enabled=False)

        self.assertFalse(plugin.enabled)

    def test_exported_capabilities_defaults_to_empty(self):
        plugin = Plugin(name="Core", version="1.0", author="x", description="d")

        self.assertEqual(plugin.exported_capabilities, ())

    def test_exported_capabilities_honored(self):
        capability = _capability()
        plugin = Plugin(
            name="Core", version="1.0", author="x", description="d",
            exported_capabilities=[capability],
        )

        self.assertEqual(plugin.exported_capabilities, (capability,))

    def test_metadata_defaults_to_empty(self):
        plugin = Plugin(name="Core", version="1.0", author="x", description="d")

        self.assertEqual(dict(plugin.metadata), {})

    def test_metadata_honored(self):
        plugin = Plugin(
            name="Core", version="1.0", author="x", description="d",
            metadata={"source": "package_014"},
        )

        self.assertEqual(plugin.metadata["source"], "package_014")

    def test_multiple_exported_capabilities_supported(self):
        cap_a = _capability(name="A")
        cap_b = _capability(name="B", intent_types=[IntentType.COMMAND])
        plugin = Plugin(
            name="Core", version="1.0", author="x", description="d",
            exported_capabilities=[cap_a, cap_b],
        )

        self.assertEqual(plugin.exported_capabilities, (cap_a, cap_b))


class PluginImmutabilityTests(unittest.TestCase):
    def setUp(self):
        self.capability = _capability()
        self.plugin = Plugin(
            name="Core", version="1.0", author="x", description="d",
            exported_capabilities=[self.capability],
            metadata={"k": "v"},
        )

    def test_is_frozen(self):
        with self.assertRaises(Exception):
            self.plugin.name = "Changed"

    def test_exported_capabilities_is_a_tuple(self):
        self.assertIsInstance(self.plugin.exported_capabilities, tuple)

    def test_exported_capabilities_immutable_from_source_list(self):
        source = [self.capability]
        plugin = Plugin(
            name="Core", version="1.0", author="x", description="d",
            exported_capabilities=source,
        )
        source.append(_capability(name="Other"))

        self.assertEqual(plugin.exported_capabilities, (self.capability,))

    def test_metadata_is_mapping_proxy(self):
        self.assertIsInstance(self.plugin.metadata, MappingProxyType)

    def test_metadata_cannot_be_mutated(self):
        with self.assertRaises(TypeError):
            self.plugin.metadata["k"] = "changed"

    def test_metadata_immutable_from_source_dict(self):
        source = {"k": "v"}
        plugin = Plugin(
            name="Core", version="1.0", author="x", description="d", metadata=source
        )
        source["k"] = "changed"

        self.assertEqual(plugin.metadata["k"], "v")


if __name__ == "__main__":
    unittest.main()
