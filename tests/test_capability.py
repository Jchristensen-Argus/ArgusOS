"""Unit tests for argus.capability.capability.Capability."""

import dataclasses
import unittest
from types import MappingProxyType

from argus.capability import Capability, CapabilityMetadata
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


# -- Package 033: version / capability_metadata --------------------------


class VersionFieldTests(unittest.TestCase):
    def test_version_defaults_to_1_0(self):
        capability = Capability(
            name="Answer", description="d", intent_types=[IntentType.QUESTION], action_kind="workflow"
        )
        self.assertEqual(capability.version, "1.0")

    def test_version_honored(self):
        capability = Capability(
            name="Answer",
            description="d",
            intent_types=[IntentType.QUESTION],
            action_kind="workflow",
            version="2.0",
        )
        self.assertEqual(capability.version, "2.0")

    def test_version_field_cannot_be_reassigned(self):
        capability = Capability(
            name="Answer", description="d", intent_types=[IntentType.QUESTION], action_kind="workflow"
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            capability.version = "9.9"


class CapabilityMetadataFieldTests(unittest.TestCase):
    def test_capability_metadata_defaults_to_a_fresh_instance(self):
        capability = Capability(
            name="Answer", description="d", intent_types=[IntentType.QUESTION], action_kind="workflow"
        )
        self.assertIsInstance(capability.capability_metadata, CapabilityMetadata)

    def test_default_capability_metadata_is_a_fresh_instance_per_capability(self):
        a = Capability(name="A", description="d", intent_types=[IntentType.QUESTION], action_kind="workflow")
        b = Capability(name="B", description="d", intent_types=[IntentType.QUESTION], action_kind="workflow")
        self.assertIsNot(a.capability_metadata, b.capability_metadata)

    def test_capability_metadata_honored(self):
        metadata = CapabilityMetadata(extra={"k": "v"})
        capability = Capability(
            name="Answer",
            description="d",
            intent_types=[IntentType.QUESTION],
            action_kind="workflow",
            capability_metadata=metadata,
        )
        self.assertIs(capability.capability_metadata, metadata)

    def test_capability_metadata_field_cannot_be_reassigned(self):
        capability = Capability(
            name="Answer", description="d", intent_types=[IntentType.QUESTION], action_kind="workflow"
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            capability.capability_metadata = CapabilityMetadata()

    def test_capability_metadata_is_distinct_from_the_pre_existing_metadata_field(self):
        # Package 033: capability_metadata (CapabilityMetadata, new)
        # and metadata (Mapping[str, Any], pre-existing since 013) are
        # two separate fields - populating one never touches the
        # other. See capability.py's own module docstring.
        capability = Capability(
            name="Answer",
            description="d",
            intent_types=[IntentType.QUESTION],
            action_kind="workflow",
            metadata={"caller": "data"},
            capability_metadata=CapabilityMetadata(extra={"bookkeeping": "data"}),
        )
        self.assertEqual(dict(capability.metadata), {"caller": "data"})
        self.assertEqual(dict(capability.capability_metadata.extra), {"bookkeeping": "data"})


class BackwardCompatibilityTests(unittest.TestCase):
    # Package 033: every pre-existing (013) field, and every
    # pre-existing call shape, must keep working unchanged - this
    # class exists solely to make that guarantee explicit and
    # regression-tested, beyond what the tests above already cover
    # incidentally.

    def test_field_set_gained_exactly_two_new_fields(self):
        field_names = {f.name for f in dataclasses.fields(Capability)}
        self.assertEqual(
            field_names,
            {
                "name",
                "description",
                "intent_types",
                "action_kind",
                "id",
                "workflow_id",
                "enabled",
                "version",
                "metadata",
                "capability_metadata",
            },
        )

    def test_pre_existing_positional_keyword_construction_still_works(self):
        capability = Capability(
            name="Answer",
            description="Answers questions.",
            intent_types=[IntentType.QUESTION],
            action_kind="workflow",
            id="fixed-id",
            workflow_id="answer_workflow",
            enabled=True,
            metadata={"source": "package_012"},
        )
        self.assertEqual(capability.id, "fixed-id")
        self.assertEqual(capability.metadata["source"], "package_012")
        # New fields still default even when every pre-existing field
        # is supplied explicitly.
        self.assertEqual(capability.version, "1.0")
        self.assertIsInstance(capability.capability_metadata, CapabilityMetadata)


if __name__ == "__main__":
    unittest.main()
