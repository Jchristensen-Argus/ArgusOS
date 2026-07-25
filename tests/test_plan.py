"""Unit tests for argus.planner.plan.Plan and PlanStatus."""

import unittest
from datetime import datetime
from types import MappingProxyType

from argus.intent import Intent, IntentType
from argus.planner import Plan, PlanStatus, PlanStep


def _intent(**overrides):
    defaults = dict(name=IntentType.QUESTION, confidence=0.9)
    defaults.update(overrides)
    return Intent(**defaults)


class PlanStatusTests(unittest.TestCase):
    def test_all_five_values_exist(self):
        self.assertEqual(PlanStatus.CREATED.value, "created")
        self.assertEqual(PlanStatus.VALIDATED.value, "validated")
        self.assertEqual(PlanStatus.READY.value, "ready")
        self.assertEqual(PlanStatus.FAILED.value, "failed")
        self.assertEqual(PlanStatus.COMPLETED.value, "completed")


class PlanConstructionTests(unittest.TestCase):
    def test_minimal_construction(self):
        intent = _intent()
        plan = Plan(originating_intent=intent)

        self.assertIs(plan.originating_intent, intent)

    def test_id_auto_generated_and_unique(self):
        a = Plan(originating_intent=_intent())
        b = Plan(originating_intent=_intent())

        self.assertTrue(a.id)
        self.assertNotEqual(a.id, b.id)

    def test_explicit_id_honored(self):
        plan = Plan(originating_intent=_intent(), id="fixed-id")

        self.assertEqual(plan.id, "fixed-id")

    def test_status_defaults_to_created(self):
        plan = Plan(originating_intent=_intent())

        self.assertEqual(plan.status, PlanStatus.CREATED)

    def test_status_honored(self):
        plan = Plan(originating_intent=_intent(), status=PlanStatus.VALIDATED)

        self.assertEqual(plan.status, PlanStatus.VALIDATED)

    def test_created_at_auto_generated(self):
        plan = Plan(originating_intent=_intent())

        self.assertIsInstance(plan.created_at, datetime)

    def test_steps_defaults_to_empty(self):
        plan = Plan(originating_intent=_intent())

        self.assertEqual(plan.steps, ())

    def test_steps_honored(self):
        step = PlanStep(description="A", required_capability="cap-1")
        plan = Plan(originating_intent=_intent(), steps=[step])

        self.assertEqual(plan.steps, (step,))

    def test_metadata_defaults_to_empty(self):
        plan = Plan(originating_intent=_intent())

        self.assertEqual(dict(plan.metadata), {})

    def test_metadata_honored(self):
        plan = Plan(originating_intent=_intent(), metadata={"source": "package_015"})

        self.assertEqual(plan.metadata["source"], "package_015")


class PlanImmutabilityTests(unittest.TestCase):
    def setUp(self):
        self.step = PlanStep(description="A", required_capability="cap-1")
        self.plan = Plan(
            originating_intent=_intent(), steps=[self.step], metadata={"k": "v"}
        )

    def test_is_frozen(self):
        with self.assertRaises(Exception):
            self.plan.status = PlanStatus.VALIDATED

    def test_steps_is_a_tuple(self):
        self.assertIsInstance(self.plan.steps, tuple)

    def test_steps_immutable_from_source_list(self):
        source = [self.step]
        plan = Plan(originating_intent=_intent(), steps=source)
        source.append(PlanStep(description="B", required_capability="cap-2"))

        self.assertEqual(plan.steps, (self.step,))

    def test_metadata_is_mapping_proxy(self):
        self.assertIsInstance(self.plan.metadata, MappingProxyType)

    def test_metadata_cannot_be_mutated(self):
        with self.assertRaises(TypeError):
            self.plan.metadata["k"] = "changed"

    def test_metadata_immutable_from_source_dict(self):
        source = {"k": "v"}
        plan = Plan(originating_intent=_intent(), metadata=source)
        source["k"] = "changed"

        self.assertEqual(plan.metadata["k"], "v")


if __name__ == "__main__":
    unittest.main()
