"""Unit tests for argus.capability.capability.Capability."""

import unittest
from types import MappingProxyType

from argus.capability import Capability
from argus.intent import IntentType


class CapabilityConstructionTests(unittest.TestCase):
    def test_minimal_construction(self):
        capability = Capability(
            name="Answer",
            description="Answers questions.",
            intent_types=[IntentType.QUESTION],
            action_kind="workflow",
        )

        self.assertEqual(capability.name, "Answer")
        self.assertEqual(capability.description, "Answers questions.")
        self.assertEqual(capability.intent_types, (IntentType.QUESTION,))
        self.assertEqual(capability.action_kind, "workflow")

    def test_id_auto_generated_and_unique(self):
        a = Capability(name="A", description="d", intent_types=[IntentType.QUESTION], action_kind="workflow")
        b = Capability(name="B", description="d", intent_types=[IntentType.QUESTION], action_kind="workflow")

        self.assertTrue(a.id)
        self.assertNotEqual(a.id, b.id)

    def test_explicit_id_honored(self):
        capability = Capability(
            name="Answer",
            description="d",
            intent_types=[IntentType.QUESTION],
            action_kind="workflow",
            id="fixed-id",
        )

        self.assertEqual(capability.id, "fixed-id")

    def test_workflow_id_defaults_to_none(self):
        capability = Capability(
            name="Answer", description="d", intent_types=[IntentType.QUESTION], action_kind="workflow"
        )

        self.assertIsNone(capability.workflow_id)

    def test_workflow_id_honored(self):
        capability = Capability(
            name="Answer",
            description="d",
            intent_types=[IntentType.QUESTION],
            action_kind="workflow",
            workflow_id="answer_workflow",
        )

        self.assertEqual(capability.workflow_id, "answer_workflow")

    def test_enabled_defaults_to_true(self):
        capability = Capability(
            name="Answer", description="d", intent_types=[IntentType.QUESTION], action_kind="workflow"
        )

        self.assertTrue(capability.enabled)

    def test_enabled_honored(self):
        capability = Capability(
            name="Answer",
            description="d",
            intent_types=[IntentType.QUESTION],
            action_kind="workflow",
            enabled=False,
        )

        self.assertFalse(capability.enabled)

    def test_metadata_defaults_to_empty(self):
        capability = Capability(
            name="Answer", description="d", intent_types=[IntentType.QUESTION], action_kind="workflow"
        )

        self.assertEqual(dict(capability.metadata), {})

    def test_metadata_honored(self):
        capability = Capability(
            name="Answer",
            description="d",
            intent_types=[IntentType.QUESTION],
            action_kind="workflow",
            metadata={"source": "package_012"},
        )

        self.assertEqual(capability.metadata["source"], "package_012")

    def test_multiple_intent_types_supported(self):
        capability = Capability(
            name="Multi",
            description="d",
            intent_types=[IntentType.QUESTION, IntentType.UNKNOWN],
            action_kind="workflow",
        )

        self.assertEqual(capability.intent_types, (IntentType.QUESTION, IntentType.UNKNOWN))


class CapabilityImmutabilityTests(unittest.TestCase):
    def setUp(self):
        self.capability = Capability(
            name="Answer",
            description="d",
            intent_types=[IntentType.QUESTION],
            action_kind="workflow",
            metadata={"k": "v"},
        )

    def test_is_frozen(self):
        with self.assertRaises(Exception):
            self.capability.name = "Changed"

    def test_intent_types_is_a_tuple(self):
        self.assertIsInstance(self.capability.intent_types, tuple)

    def test_intent_types_immutable_from_source_list(self):
        source = [IntentType.QUESTION]
        capability = Capability(
            name="Answer", description="d", intent_types=source, action_kind="workflow"
        )
        source.append(IntentType.COMMAND)

        self.assertEqual(capability.intent_types, (IntentType.QUESTION,))

    def test_metadata_is_mapping_proxy(self):
        self.assertIsInstance(self.capability.metadata, MappingProxyType)

    def test_metadata_cannot_be_mutated(self):
        with self.assertRaises(TypeError):
            self.capability.metadata["k"] = "changed"

    def test_metadata_immutable_from_source_dict(self):
        source = {"k": "v"}
        capability = Capability(
            name="Answer",
            description="d",
            intent_types=[IntentType.QUESTION],
            action_kind="workflow",
            metadata=source,
        )
        source["k"] = "mutated"

        self.assertEqual(capability.metadata["k"], "v")


if __name__ == "__main__":
    unittest.main()
