"""Unit tests for argus.goal.metadata.GoalMetadata."""

import dataclasses
import unittest
from datetime import datetime

from argus.goal import GOAL_METADATA_VERSION, GoalMetadata


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        metadata = GoalMetadata()
        self.assertIsInstance(metadata.created_at, datetime)
        self.assertEqual(metadata.version, GOAL_METADATA_VERSION)
        self.assertTrue(metadata.correlation_id)
        self.assertIsNone(metadata.owner)
        self.assertEqual(metadata.tags, ())
        self.assertEqual(dict(metadata.extra), {})

    def test_all_fields_set(self):
        created_at = datetime(2026, 1, 1)
        metadata = GoalMetadata(
            created_at=created_at,
            version="9.9",
            correlation_id="fixed-id",
            owner="Jane",
            tags=["q1", "growth"],
            extra={"k": "v"},
        )
        self.assertEqual(metadata.created_at, created_at)
        self.assertEqual(metadata.version, "9.9")
        self.assertEqual(metadata.correlation_id, "fixed-id")
        self.assertEqual(metadata.owner, "Jane")
        self.assertEqual(metadata.tags, ("q1", "growth"))
        self.assertEqual(dict(metadata.extra), {"k": "v"})

    def test_default_correlation_id_is_unique_per_instance(self):
        a = GoalMetadata()
        b = GoalMetadata()
        self.assertNotEqual(a.correlation_id, b.correlation_id)


class FieldOrderTests(unittest.TestCase):
    def test_field_order_places_extra_last(self):
        # This package's own literal field list is "created_at, owner,
        # correlation_id, version, tags, extra" - resolved by
        # following ProjectMetadata's/WorkspaceMetadata's own
        # established precedent instead: created_at, version,
        # correlation_id, owner, tags, extra. See metadata.py's own
        # module docstring.
        field_names = [f.name for f in dataclasses.fields(GoalMetadata)]
        self.assertEqual(
            field_names,
            ["created_at", "version", "correlation_id", "owner", "tags", "extra"],
        )


class OwnerTests(unittest.TestCase):
    def test_owner_defaults_to_none(self):
        self.assertIsNone(GoalMetadata().owner)

    def test_owner_accepts_a_string(self):
        self.assertEqual(GoalMetadata(owner="Jane").owner, "Jane")


class TagsTests(unittest.TestCase):
    def test_tags_default_to_empty_tuple(self):
        self.assertEqual(GoalMetadata().tags, ())

    def test_tags_are_wrapped_in_a_tuple_regardless_of_input_sequence_type(self):
        self.assertEqual(GoalMetadata(tags=["a", "b"]).tags, ("a", "b"))
        self.assertEqual(GoalMetadata(tags=("a", "b")).tags, ("a", "b"))

    def test_tags_defensive_copy_not_shared_with_caller(self):
        original = ["a", "b"]
        metadata = GoalMetadata(tags=original)
        original.append("c")
        self.assertEqual(metadata.tags, ("a", "b"))


class ExtraTests(unittest.TestCase):
    def test_extra_is_wrapped_in_mappingproxytype(self):
        metadata = GoalMetadata(extra={"a": 1})
        self.assertNotIsInstance(metadata.extra, dict)
        self.assertEqual(metadata.extra["a"], 1)

    def test_extra_defensive_copy_not_shared_with_caller(self):
        original = {"a": 1}
        metadata = GoalMetadata(extra=original)
        original["a"] = 999
        self.assertEqual(metadata.extra["a"], 1)

    def test_extra_is_immutable(self):
        metadata = GoalMetadata(extra={"a": 1})
        with self.assertRaises(TypeError):
            metadata.extra["a"] = 2


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        metadata = GoalMetadata()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            metadata.version = "2.0"

    def test_tags_field_immutable(self):
        metadata = GoalMetadata()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            metadata.tags = ("x",)


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        created_at = datetime(2026, 1, 1)
        a = GoalMetadata(created_at=created_at, correlation_id="c1")
        b = GoalMetadata(created_at=created_at, correlation_id="c1")
        self.assertEqual(a, b)

    def test_not_equal_when_correlation_id_differs(self):
        created_at = datetime(2026, 1, 1)
        a = GoalMetadata(created_at=created_at, correlation_id="c1")
        b = GoalMetadata(created_at=created_at, correlation_id="c2")
        self.assertNotEqual(a, b)

    def test_not_equal_when_owner_differs(self):
        created_at = datetime(2026, 1, 1)
        a = GoalMetadata(created_at=created_at, correlation_id="c1", owner="Jane")
        b = GoalMetadata(created_at=created_at, correlation_id="c1", owner="Bob")
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
