"""Unit tests for argus.automation.builder.AutomationBuilder."""

import unittest

from argus.automation import (
    AutomationBuilder,
    AutomationStatus,
    AutomationTrigger,
    IAutomationBuilder,
    InvalidAutomationError,
)


class IdentityTests(unittest.TestCase):
    def test_is_an_iautomationbuilder(self):
        self.assertIsInstance(AutomationBuilder(), IAutomationBuilder)

    def test_is_not_an_iservice(self):
        from argus.lifecycle import IService

        self.assertNotIsInstance(AutomationBuilder(), IService)

    def test_starts_with_default_values(self):
        automation = AutomationBuilder().build()
        self.assertEqual(automation.name, "")
        self.assertEqual(automation.description, "")
        self.assertEqual(automation.status, AutomationStatus.ACTIVE)
        self.assertEqual(automation.trigger, AutomationTrigger.MANUAL)

    def test_constructor_takes_no_arguments(self):
        builder = AutomationBuilder()
        self.assertIsInstance(builder, AutomationBuilder)

    def test_no_with_automation_id_method_exists(self):
        self.assertFalse(hasattr(AutomationBuilder(), "with_automation_id"))

    def test_no_with_owner_method_exists(self):
        self.assertFalse(hasattr(AutomationBuilder(), "with_owner"))

    def test_no_with_tags_method_exists(self):
        self.assertFalse(hasattr(AutomationBuilder(), "with_tags"))

    def test_has_with_trigger_method(self):
        # Unlike owner/tags, trigger is explicitly named in this
        # package's own Responsibilities list - see builder.py's own
        # module docstring.
        self.assertTrue(hasattr(AutomationBuilder(), "with_trigger"))


class WithNameTests(unittest.TestCase):
    def test_with_name_returns_self_for_chaining(self):
        builder = AutomationBuilder()
        result = builder.with_name("Nightly report")
        self.assertIs(result, builder)

    def test_with_name_is_overwritten_not_accumulated(self):
        automation = (
            AutomationBuilder().with_name("First").with_name("Second").build()
        )
        self.assertEqual(automation.name, "Second")

    def test_with_name_rejects_empty_string(self):
        with self.assertRaises(InvalidAutomationError):
            AutomationBuilder().with_name("")

    def test_with_name_rejects_non_string(self):
        with self.assertRaises(InvalidAutomationError):
            AutomationBuilder().with_name(123)

    def test_with_name_rejects_none(self):
        with self.assertRaises(InvalidAutomationError):
            AutomationBuilder().with_name(None)


class WithDescriptionTests(unittest.TestCase):
    def test_with_description_returns_self_for_chaining(self):
        builder = AutomationBuilder()
        result = builder.with_description("Generate the nightly sales report")
        self.assertIs(result, builder)

    def test_with_description_is_overwritten_not_accumulated(self):
        automation = (
            AutomationBuilder()
            .with_description("First")
            .with_description("Second")
            .build()
        )
        self.assertEqual(automation.description, "Second")

    def test_with_description_accepts_empty_string(self):
        automation = AutomationBuilder().with_description("").build()
        self.assertEqual(automation.description, "")

    def test_with_description_rejects_non_string(self):
        with self.assertRaises(InvalidAutomationError):
            AutomationBuilder().with_description(123)

    def test_with_description_rejects_none(self):
        with self.assertRaises(InvalidAutomationError):
            AutomationBuilder().with_description(None)


class WithStatusTests(unittest.TestCase):
    def test_with_status_returns_self_for_chaining(self):
        builder = AutomationBuilder()
        result = builder.with_status(AutomationStatus.PAUSED)
        self.assertIs(result, builder)

    def test_with_status_is_overwritten_not_accumulated(self):
        automation = (
            AutomationBuilder()
            .with_status(AutomationStatus.PAUSED)
            .with_status(AutomationStatus.DISABLED)
            .build()
        )
        self.assertEqual(automation.status, AutomationStatus.DISABLED)

    def test_with_status_rejects_non_status(self):
        with self.assertRaises(InvalidAutomationError):
            AutomationBuilder().with_status("active")

    def test_with_status_rejects_none(self):
        with self.assertRaises(InvalidAutomationError):
            AutomationBuilder().with_status(None)

    def test_default_status_is_active(self):
        automation = AutomationBuilder().build()
        self.assertEqual(automation.status, AutomationStatus.ACTIVE)


class WithTriggerTests(unittest.TestCase):
    def test_with_trigger_returns_self_for_chaining(self):
        builder = AutomationBuilder()
        result = builder.with_trigger(AutomationTrigger.EVENT)
        self.assertIs(result, builder)

    def test_with_trigger_is_overwritten_not_accumulated(self):
        automation = (
            AutomationBuilder()
            .with_trigger(AutomationTrigger.EVENT)
            .with_trigger(AutomationTrigger.CONDITION)
            .build()
        )
        self.assertEqual(automation.trigger, AutomationTrigger.CONDITION)

    def test_with_trigger_rejects_non_trigger(self):
        with self.assertRaises(InvalidAutomationError):
            AutomationBuilder().with_trigger("manual")

    def test_with_trigger_rejects_none(self):
        with self.assertRaises(InvalidAutomationError):
            AutomationBuilder().with_trigger(None)

    def test_default_trigger_is_manual(self):
        automation = AutomationBuilder().build()
        self.assertEqual(automation.trigger, AutomationTrigger.MANUAL)


class WithMetadataTests(unittest.TestCase):
    def test_with_metadata_returns_self_for_chaining(self):
        builder = AutomationBuilder()
        result = builder.with_metadata("k", "v")
        self.assertIs(result, builder)

    def test_with_metadata_populates_extra(self):
        automation = AutomationBuilder().with_metadata("frequency", "daily").build()
        self.assertEqual(automation.metadata.extra["frequency"], "daily")

    def test_with_metadata_accumulates_distinct_keys(self):
        automation = (
            AutomationBuilder().with_metadata("a", 1).with_metadata("b", 2).build()
        )
        self.assertEqual(dict(automation.metadata.extra), {"a": 1, "b": 2})

    def test_with_metadata_same_key_overwrites(self):
        automation = (
            AutomationBuilder()
            .with_metadata("k", "first")
            .with_metadata("k", "second")
            .build()
        )
        self.assertEqual(automation.metadata.extra["k"], "second")

    def test_with_metadata_rejects_empty_key(self):
        with self.assertRaises(InvalidAutomationError):
            AutomationBuilder().with_metadata("", "v")

    def test_with_metadata_rejects_non_string_key(self):
        with self.assertRaises(InvalidAutomationError):
            AutomationBuilder().with_metadata(123, "v")

    def test_with_metadata_cannot_set_owner_or_tags(self):
        automation = AutomationBuilder().with_metadata("owner", "Jane").build()
        self.assertIsNone(automation.metadata.owner)
        self.assertEqual(automation.metadata.extra["owner"], "Jane")


class BuildTests(unittest.TestCase):
    def test_build_with_no_calls_produces_a_default_automation(self):
        automation = AutomationBuilder().build()
        self.assertEqual(automation.name, "")
        self.assertEqual(automation.description, "")
        self.assertEqual(automation.status, AutomationStatus.ACTIVE)
        self.assertEqual(automation.trigger, AutomationTrigger.MANUAL)

    def test_build_produces_a_fresh_automation_id_each_call(self):
        builder = AutomationBuilder().with_name("Nightly report")
        first = builder.build()
        second = builder.build()
        self.assertNotEqual(first.automation_id, second.automation_id)

    def test_build_after_build_does_not_mutate_the_earlier_automation(self):
        builder = AutomationBuilder().with_name("First")
        first = builder.build()
        builder.with_name("Second")
        second = builder.build()
        self.assertEqual(first.name, "First")
        self.assertEqual(second.name, "Second")

    def test_full_chain_produces_the_expected_automation(self):
        automation = (
            AutomationBuilder()
            .with_name("Nightly report")
            .with_description("Generate the nightly sales report")
            .with_status(AutomationStatus.ACTIVE)
            .with_trigger(AutomationTrigger.SCHEDULE)
            .with_metadata("k", "v")
            .build()
        )
        self.assertEqual(automation.name, "Nightly report")
        self.assertEqual(automation.description, "Generate the nightly sales report")
        self.assertEqual(automation.status, AutomationStatus.ACTIVE)
        self.assertEqual(automation.trigger, AutomationTrigger.SCHEDULE)
        self.assertEqual(automation.metadata.extra["k"], "v")


if __name__ == "__main__":
    unittest.main()
