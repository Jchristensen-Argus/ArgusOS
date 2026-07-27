"""Unit tests for argus.automation.automation.Automation."""

import copy
import dataclasses
import pickle
import unittest

from argus.automation import Automation, AutomationMetadata, AutomationStatus, AutomationTrigger


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        automation = Automation()
        self.assertTrue(automation.automation_id)
        self.assertEqual(automation.name, "")
        self.assertEqual(automation.description, "")
        self.assertEqual(automation.status, AutomationStatus.ACTIVE)
        self.assertEqual(automation.trigger, AutomationTrigger.MANUAL)
        self.assertIsInstance(automation.metadata, AutomationMetadata)

    def test_all_fields_set(self):
        metadata = AutomationMetadata(extra={"k": "v"})
        automation = Automation(
            automation_id="fixed-id",
            name="Nightly report",
            description="Generate the nightly sales report",
            status=AutomationStatus.PAUSED,
            trigger=AutomationTrigger.SCHEDULE,
            metadata=metadata,
        )
        self.assertEqual(automation.automation_id, "fixed-id")
        self.assertEqual(automation.name, "Nightly report")
        self.assertEqual(automation.description, "Generate the nightly sales report")
        self.assertEqual(automation.status, AutomationStatus.PAUSED)
        self.assertEqual(automation.trigger, AutomationTrigger.SCHEDULE)
        self.assertIs(automation.metadata, metadata)

    def test_default_automation_id_is_unique_per_instance(self):
        a = Automation()
        b = Automation()
        self.assertNotEqual(a.automation_id, b.automation_id)


class FieldOrderTests(unittest.TestCase):
    def test_field_order_places_metadata_last(self):
        field_names = [f.name for f in dataclasses.fields(Automation)]
        self.assertEqual(
            field_names,
            ["automation_id", "name", "description", "status", "trigger", "metadata"],
        )


class DefaultStatusAndTriggerTests(unittest.TestCase):
    def test_default_status_is_active(self):
        # Matches PolicyStatus's/WorkspaceStatus's own default, since
        # neither its own nor those member lists name a "not yet
        # begun" state - see status.py's own module docstring.
        self.assertEqual(Automation().status, AutomationStatus.ACTIVE)

    def test_default_trigger_is_manual(self):
        self.assertEqual(Automation().trigger, AutomationTrigger.MANUAL)


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        automation = Automation()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            automation.automation_id = "mutated"

    def test_name_field_immutable(self):
        automation = Automation()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            automation.name = "mutated"

    def test_trigger_field_immutable(self):
        automation = Automation()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            automation.trigger = AutomationTrigger.EVENT

    def test_metadata_field_immutable(self):
        automation = Automation()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            automation.metadata = AutomationMetadata()


class MiscellaneousRobustnessTests(unittest.TestCase):
    def test_deepcopy_of_scalar_fields_round_trips_equal(self):
        automation = Automation()
        copied_id = copy.deepcopy(automation.automation_id)
        self.assertEqual(copied_id, automation.automation_id)

    def test_pickle_of_scalar_fields_round_trips_equal(self):
        automation = Automation()
        self.assertEqual(
            pickle.loads(pickle.dumps(automation.automation_id)),
            automation.automation_id,
        )
        self.assertIs(pickle.loads(pickle.dumps(automation.status)), automation.status)
        self.assertIs(pickle.loads(pickle.dumps(automation.trigger)), automation.trigger)

    def test_automation_id_is_a_plain_string_suitable_for_json(self):
        automation = Automation()
        self.assertIsInstance(automation.automation_id, str)


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        metadata = AutomationMetadata()
        a = Automation(automation_id="a1", name="Nightly report", metadata=metadata)
        b = Automation(automation_id="a1", name="Nightly report", metadata=metadata)
        self.assertEqual(a, b)

    def test_not_equal_when_automation_id_differs(self):
        metadata = AutomationMetadata()
        a = Automation(automation_id="a1", metadata=metadata)
        b = Automation(automation_id="a2", metadata=metadata)
        self.assertNotEqual(a, b)

    def test_not_equal_when_trigger_differs(self):
        metadata = AutomationMetadata()
        a = Automation(automation_id="a1", trigger=AutomationTrigger.MANUAL, metadata=metadata)
        b = Automation(automation_id="a1", trigger=AutomationTrigger.EVENT, metadata=metadata)
        self.assertNotEqual(a, b)

    def test_not_equal_when_status_differs(self):
        metadata = AutomationMetadata()
        a = Automation(automation_id="a1", status=AutomationStatus.ACTIVE, metadata=metadata)
        b = Automation(automation_id="a1", status=AutomationStatus.ARCHIVED, metadata=metadata)
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
