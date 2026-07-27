"""Unit tests for argus.capability.builder.CapabilityBuilder."""

import unittest

from argus.capability import (
    Capability,
    CapabilityBuilder,
    ICapabilityBuilder,
    InvalidCapabilityError,
)
from argus.intent import IntentType


class IdentityTests(unittest.TestCase):
    def test_is_an_icapabilitybuilder(self):
        self.assertIsInstance(CapabilityBuilder(), ICapabilityBuilder)

    def test_is_not_an_iservice(self):
        from argus.lifecycle import IService

        self.assertNotIsInstance(CapabilityBuilder(), IService)

    def test_starts_with_default_values(self):
        capability = CapabilityBuilder().build()
        self.assertEqual(capability.name, "")
        self.assertEqual(capability.description, "")
        self.assertEqual(capability.intent_types, ())
        self.assertEqual(capability.action_kind, "")
        self.assertIsNone(capability.workflow_id)
        self.assertTrue(capability.enabled)
        self.assertEqual(capability.version, "1.0")

    def test_constructor_takes_no_arguments(self):
        builder = CapabilityBuilder()
        self.assertIsInstance(builder, CapabilityBuilder)


class WithIdTests(unittest.TestCase):
    def test_with_id_returns_self_for_chaining(self):
        builder = CapabilityBuilder()
        result = builder.with_id("cap-1")
        self.assertIs(result, builder)

    def test_with_id_is_overwritten_not_accumulated(self):
        capability = CapabilityBuilder().with_id("first").with_id("second").build()
        self.assertEqual(capability.id, "second")

    def test_without_with_id_a_fresh_id_is_auto_generated(self):
        a = CapabilityBuilder().build()
        b = CapabilityBuilder().build()
        self.assertTrue(a.id)
        self.assertNotEqual(a.id, b.id)

    def test_with_id_rejects_empty_string(self):
        with self.assertRaises(InvalidCapabilityError):
            CapabilityBuilder().with_id("")

    def test_with_id_rejects_non_string(self):
        with self.assertRaises(InvalidCapabilityError):
            CapabilityBuilder().with_id(123)


class WithNameTests(unittest.TestCase):
    def test_with_name_returns_self_for_chaining(self):
        builder = CapabilityBuilder()
        result = builder.with_name("Answer")
        self.assertIs(result, builder)

    def test_with_name_is_overwritten_not_accumulated(self):
        capability = CapabilityBuilder().with_name("A").with_name("B").build()
        self.assertEqual(capability.name, "B")

    def test_with_name_rejects_empty_string(self):
        with self.assertRaises(InvalidCapabilityError):
            CapabilityBuilder().with_name("")

    def test_with_name_rejects_non_string(self):
        with self.assertRaises(InvalidCapabilityError):
            CapabilityBuilder().with_name(123)


class WithDescriptionTests(unittest.TestCase):
    def test_with_description_returns_self_for_chaining(self):
        builder = CapabilityBuilder()
        result = builder.with_description("d")
        self.assertIs(result, builder)

    def test_with_description_is_overwritten_not_accumulated(self):
        capability = CapabilityBuilder().with_description("A").with_description("B").build()
        self.assertEqual(capability.description, "B")

    def test_with_description_accepts_empty_string(self):
        # Unlike name/action_kind, Capability.register() itself never
        # requires a non-empty description - see registry.py's own
        # _validate_capability().
        capability = CapabilityBuilder().with_description("").build()
        self.assertEqual(capability.description, "")

    def test_with_description_rejects_non_string(self):
        with self.assertRaises(InvalidCapabilityError):
            CapabilityBuilder().with_description(123)


class WithIntentTypeTests(unittest.TestCase):
    def test_with_intent_type_returns_self_for_chaining(self):
        builder = CapabilityBuilder()
        result = builder.with_intent_type(IntentType.QUESTION)
        self.assertIs(result, builder)

    def test_with_intent_type_accumulates_in_call_order(self):
        capability = (
            CapabilityBuilder()
            .with_intent_type(IntentType.QUESTION)
            .with_intent_type(IntentType.COMMAND)
            .build()
        )
        self.assertEqual(capability.intent_types, (IntentType.QUESTION, IntentType.COMMAND))

    def test_with_intent_type_rejects_non_intent_type(self):
        with self.assertRaises(InvalidCapabilityError):
            CapabilityBuilder().with_intent_type("question")

    def test_with_intent_type_rejects_none(self):
        with self.assertRaises(InvalidCapabilityError):
            CapabilityBuilder().with_intent_type(None)


class WithIntentTypesTests(unittest.TestCase):
    def test_with_intent_types_returns_self_for_chaining(self):
        builder = CapabilityBuilder()
        result = builder.with_intent_types([IntentType.QUESTION])
        self.assertIs(result, builder)

    def test_with_intent_types_accumulates_each_item_in_order(self):
        capability = (
            CapabilityBuilder()
            .with_intent_types([IntentType.QUESTION, IntentType.COMMAND])
            .build()
        )
        self.assertEqual(capability.intent_types, (IntentType.QUESTION, IntentType.COMMAND))

    def test_with_intent_types_accepts_a_tuple(self):
        capability = CapabilityBuilder().with_intent_types((IntentType.QUESTION,)).build()
        self.assertEqual(capability.intent_types, (IntentType.QUESTION,))

    def test_with_intent_types_combines_with_prior_calls(self):
        capability = (
            CapabilityBuilder()
            .with_intent_type(IntentType.QUESTION)
            .with_intent_types([IntentType.COMMAND])
            .build()
        )
        self.assertEqual(capability.intent_types, (IntentType.QUESTION, IntentType.COMMAND))

    def test_with_intent_types_rejects_a_non_list_non_tuple(self):
        with self.assertRaises(InvalidCapabilityError):
            CapabilityBuilder().with_intent_types("not a list")

    def test_with_intent_types_rejects_a_list_containing_a_non_intent_type(self):
        with self.assertRaises(InvalidCapabilityError):
            CapabilityBuilder().with_intent_types([IntentType.QUESTION, "not one"])


class ClearIntentTypesTests(unittest.TestCase):
    def test_clear_intent_types_returns_self_for_chaining(self):
        builder = CapabilityBuilder()
        result = builder.clear_intent_types()
        self.assertIs(result, builder)

    def test_clear_intent_types_resets_to_empty(self):
        capability = (
            CapabilityBuilder()
            .with_intent_type(IntentType.QUESTION)
            .clear_intent_types()
            .build()
        )
        self.assertEqual(capability.intent_types, ())


class WithActionKindTests(unittest.TestCase):
    def test_with_action_kind_returns_self_for_chaining(self):
        builder = CapabilityBuilder()
        result = builder.with_action_kind("workflow")
        self.assertIs(result, builder)

    def test_with_action_kind_is_overwritten_not_accumulated(self):
        capability = (
            CapabilityBuilder().with_action_kind("workflow").with_action_kind("plugin").build()
        )
        self.assertEqual(capability.action_kind, "plugin")

    def test_with_action_kind_rejects_empty_string(self):
        with self.assertRaises(InvalidCapabilityError):
            CapabilityBuilder().with_action_kind("")

    def test_with_action_kind_rejects_non_string(self):
        with self.assertRaises(InvalidCapabilityError):
            CapabilityBuilder().with_action_kind(123)


class WithWorkflowIdTests(unittest.TestCase):
    def test_with_workflow_id_returns_self_for_chaining(self):
        builder = CapabilityBuilder()
        result = builder.with_workflow_id("wf-1")
        self.assertIs(result, builder)

    def test_with_workflow_id_is_overwritten_not_accumulated(self):
        capability = (
            CapabilityBuilder().with_workflow_id("wf-1").with_workflow_id("wf-2").build()
        )
        self.assertEqual(capability.workflow_id, "wf-2")

    def test_with_workflow_id_accepts_none(self):
        capability = CapabilityBuilder().with_workflow_id("wf-1").with_workflow_id(None).build()
        self.assertIsNone(capability.workflow_id)

    def test_with_workflow_id_rejects_non_string_non_none(self):
        with self.assertRaises(InvalidCapabilityError):
            CapabilityBuilder().with_workflow_id(123)


class WithEnabledTests(unittest.TestCase):
    def test_with_enabled_returns_self_for_chaining(self):
        builder = CapabilityBuilder()
        result = builder.with_enabled(False)
        self.assertIs(result, builder)

    def test_with_enabled_is_overwritten_not_accumulated(self):
        capability = CapabilityBuilder().with_enabled(False).with_enabled(True).build()
        self.assertTrue(capability.enabled)

    def test_with_enabled_defaults_to_true(self):
        capability = CapabilityBuilder().build()
        self.assertTrue(capability.enabled)

    def test_with_enabled_rejects_non_bool(self):
        with self.assertRaises(InvalidCapabilityError):
            CapabilityBuilder().with_enabled("false")


class WithVersionTests(unittest.TestCase):
    def test_with_version_returns_self_for_chaining(self):
        builder = CapabilityBuilder()
        result = builder.with_version("2.0")
        self.assertIs(result, builder)

    def test_with_version_is_overwritten_not_accumulated(self):
        capability = CapabilityBuilder().with_version("2.0").with_version("3.0").build()
        self.assertEqual(capability.version, "3.0")

    def test_with_version_defaults_to_1_0(self):
        capability = CapabilityBuilder().build()
        self.assertEqual(capability.version, "1.0")

    def test_with_version_rejects_empty_string(self):
        with self.assertRaises(InvalidCapabilityError):
            CapabilityBuilder().with_version("")

    def test_with_version_rejects_non_string(self):
        with self.assertRaises(InvalidCapabilityError):
            CapabilityBuilder().with_version(2.0)


class WithMetadataTests(unittest.TestCase):
    def test_with_metadata_returns_self_for_chaining(self):
        builder = CapabilityBuilder()
        result = builder.with_metadata("k", "v")
        self.assertIs(result, builder)

    def test_with_metadata_accumulates_distinct_keys(self):
        capability = (
            CapabilityBuilder().with_metadata("a", 1).with_metadata("b", 2).build()
        )
        self.assertEqual(dict(capability.capability_metadata.extra), {"a": 1, "b": 2})

    def test_with_metadata_same_key_last_call_wins(self):
        capability = (
            CapabilityBuilder().with_metadata("a", 1).with_metadata("a", 2).build()
        )
        self.assertEqual(dict(capability.capability_metadata.extra), {"a": 2})

    def test_with_metadata_rejects_empty_key(self):
        with self.assertRaises(InvalidCapabilityError):
            CapabilityBuilder().with_metadata("", "v")

    def test_with_metadata_rejects_non_string_key(self):
        with self.assertRaises(InvalidCapabilityError):
            CapabilityBuilder().with_metadata(123, "v")

    def test_with_metadata_does_not_populate_the_pre_existing_metadata_field(self):
        # Package 033: with_metadata() populates capability_metadata.
        # extra, not Capability's own pre-existing (013) bare
        # `metadata` field - see builder.py's own module docstring.
        capability = CapabilityBuilder().with_metadata("a", 1).build()
        self.assertEqual(dict(capability.metadata), {})


class BuildTests(unittest.TestCase):
    def test_build_returns_a_capability(self):
        capability = CapabilityBuilder().build()
        self.assertIsInstance(capability, Capability)

    def test_build_without_with_intent_type_produces_empty_tuple_not_an_error(self):
        capability = CapabilityBuilder().build()
        self.assertEqual(capability.intent_types, ())

    def test_independent_snapshots_earlier_build_not_mutated_by_later_calls(self):
        builder = CapabilityBuilder().with_intent_type(IntentType.QUESTION)
        first = builder.build()
        builder.with_intent_type(IntentType.COMMAND)
        second = builder.build()
        self.assertEqual(first.intent_types, (IntentType.QUESTION,))
        self.assertEqual(second.intent_types, (IntentType.QUESTION, IntentType.COMMAND))

    def test_different_builders_produce_different_capability_ids(self):
        a = CapabilityBuilder().build()
        b = CapabilityBuilder().build()
        self.assertNotEqual(a.id, b.id)

    def test_full_chain_produces_a_fully_populated_capability(self):
        capability = (
            CapabilityBuilder()
            .with_id("cap-1")
            .with_name("Answer")
            .with_description("Answers questions.")
            .with_intent_type(IntentType.QUESTION)
            .with_action_kind("workflow")
            .with_workflow_id("answer_workflow")
            .with_enabled(True)
            .with_version("2.0")
            .with_metadata("reason", "manual")
            .build()
        )
        self.assertEqual(capability.id, "cap-1")
        self.assertEqual(capability.name, "Answer")
        self.assertEqual(capability.description, "Answers questions.")
        self.assertEqual(capability.intent_types, (IntentType.QUESTION,))
        self.assertEqual(capability.action_kind, "workflow")
        self.assertEqual(capability.workflow_id, "answer_workflow")
        self.assertTrue(capability.enabled)
        self.assertEqual(capability.version, "2.0")
        self.assertEqual(dict(capability.capability_metadata.extra), {"reason": "manual"})


if __name__ == "__main__":
    unittest.main()
