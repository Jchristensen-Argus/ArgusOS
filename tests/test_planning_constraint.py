"""Unit tests for argus.planning.constraint.PlanningConstraint."""

import dataclasses
import unittest
from types import MappingProxyType

from argus.planning.constraint import PlanningConstraint


class PlanningConstraintTests(unittest.TestCase):
    def test_defaults(self):
        constraint = PlanningConstraint(name="my_constraint")
        self.assertEqual(constraint.name, "my_constraint")
        self.assertTrue(constraint.constraint_id)
        self.assertIsInstance(constraint.constraint_id, str)
        self.assertEqual(constraint.description, "")
        self.assertEqual(dict(constraint.metadata), {})

    def test_all_fields_set(self):
        constraint = PlanningConstraint(
            name="my_constraint",
            constraint_id="c-1",
            description="A constraint.",
            metadata={"foo": "bar"},
        )
        self.assertEqual(constraint.name, "my_constraint")
        self.assertEqual(constraint.constraint_id, "c-1")
        self.assertEqual(constraint.description, "A constraint.")
        self.assertEqual(dict(constraint.metadata), {"foo": "bar"})

    def test_default_constraint_id_is_unique_per_instance(self):
        first = PlanningConstraint(name="a")
        second = PlanningConstraint(name="a")
        self.assertNotEqual(first.constraint_id, second.constraint_id)

    def test_metadata_is_wrapped_in_mappingproxytype(self):
        constraint = PlanningConstraint(name="a", metadata={"a": 1})
        self.assertIsInstance(constraint.metadata, MappingProxyType)

    def test_metadata_defensive_copy_not_shared_with_caller(self):
        source = {"a": 1}
        constraint = PlanningConstraint(name="a", metadata=source)
        source["a"] = 999
        source["b"] = 2
        self.assertEqual(dict(constraint.metadata), {"a": 1})

    def test_metadata_is_immutable(self):
        constraint = PlanningConstraint(name="a", metadata={"a": 1})
        with self.assertRaises(TypeError):
            constraint.metadata["a"] = 2

    def test_immutability(self):
        constraint = PlanningConstraint(name="my_constraint")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            constraint.name = "changed"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            constraint.metadata = {}

    def test_equality_when_all_fields_match(self):
        first = PlanningConstraint(name="a", constraint_id="same", metadata={"k": 1})
        second = PlanningConstraint(name="a", constraint_id="same", metadata={"k": 1})
        self.assertEqual(first, second)

    def test_inequality_by_constraint_id(self):
        first = PlanningConstraint(name="a", constraint_id="x")
        second = PlanningConstraint(name="a", constraint_id="y")
        self.assertNotEqual(first, second)

    def test_inequality_by_metadata(self):
        first = PlanningConstraint(name="a", constraint_id="same", metadata={"k": 1})
        second = PlanningConstraint(name="a", constraint_id="same", metadata={"k": 2})
        self.assertNotEqual(first, second)

    def test_two_default_constructed_constraints_with_same_name_are_not_equal(self):
        first = PlanningConstraint(name="a")
        second = PlanningConstraint(name="a")
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
