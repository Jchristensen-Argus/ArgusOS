"""Unit tests for argus.planner.step.PlanStep."""

import unittest
from types import MappingProxyType

from argus.planner import PlanStep


class PlanStepConstructionTests(unittest.TestCase):
    def test_minimal_construction(self):
        step = PlanStep(description="Do the thing", required_capability="cap-1")

        self.assertEqual(step.description, "Do the thing")
        self.assertEqual(step.required_capability, "cap-1")

    def test_id_auto_generated_and_unique(self):
        a = PlanStep(description="A", required_capability="cap-1")
        b = PlanStep(description="B", required_capability="cap-1")

        self.assertTrue(a.id)
        self.assertNotEqual(a.id, b.id)

    def test_explicit_id_honored(self):
        step = PlanStep(description="A", required_capability="cap-1", id="fixed-id")

        self.assertEqual(step.id, "fixed-id")

    def test_order_defaults_to_zero(self):
        step = PlanStep(description="A", required_capability="cap-1")

        self.assertEqual(step.order, 0)

    def test_order_honored(self):
        step = PlanStep(description="A", required_capability="cap-1", order=3)

        self.assertEqual(step.order, 3)

    def test_optional_defaults_to_false(self):
        step = PlanStep(description="A", required_capability="cap-1")

        self.assertFalse(step.optional)

    def test_optional_honored(self):
        step = PlanStep(description="A", required_capability="cap-1", optional=True)

        self.assertTrue(step.optional)

    def test_metadata_defaults_to_empty(self):
        step = PlanStep(description="A", required_capability="cap-1")

        self.assertEqual(dict(step.metadata), {})

    def test_metadata_honored(self):
        step = PlanStep(
            description="A", required_capability="cap-1", metadata={"source": "package_015"}
        )

        self.assertEqual(step.metadata["source"], "package_015")


class PlanStepImmutabilityTests(unittest.TestCase):
    def setUp(self):
        self.step = PlanStep(
            description="A", required_capability="cap-1", metadata={"k": "v"}
        )

    def test_is_frozen(self):
        with self.assertRaises(Exception):
            self.step.description = "Changed"

    def test_metadata_is_mapping_proxy(self):
        self.assertIsInstance(self.step.metadata, MappingProxyType)

    def test_metadata_cannot_be_mutated(self):
        with self.assertRaises(TypeError):
            self.step.metadata["k"] = "changed"

    def test_metadata_immutable_from_source_dict(self):
        source = {"k": "v"}
        step = PlanStep(description="A", required_capability="cap-1", metadata=source)
        source["k"] = "changed"

        self.assertEqual(step.metadata["k"], "v")


if __name__ == "__main__":
    unittest.main()
