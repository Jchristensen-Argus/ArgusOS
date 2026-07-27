"""Unit tests for argus.automation.metadata.AutomationMetadata."""

import dataclasses
import unittest
from datetime import datetime

from argus.automation import AUTOMATION_METADATA_VERSION, AutomationMetadata


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        metadata = AutomationMetadata()
        self.assertIsInstance(metadata.created_at, datetime)
        self.assertEqual(metadata.version, AUTOMATION_METADATA_VERSION)
        self.assertTrue(metadata.correlation_id)
        self.assertIsNone(metadata.owner)
        self.assertEqual(metadata.tags, ())
        self.assertEqual(dict(metadata.extra), {})

    def test_all_fields_set(self):
        created_at = datetime(2026, 1, 1)
        metadata = AutomationMetadata(
            created_at=created_at,
            version="9.9",
            correlation_id="fixed-id",
            owner="Jane",
            tags=["nightly", "reporting"],
            extra={"k": "v"},
        )
        self.assertEqual(metadata.created_at, created_at)
        self.assertEqual(metadata.version, "9.9")
        self.assertEqual(metadata.correlation_id, "fixed-id")
        self.assertEqual(metadata.owner, "Jane")
        self.assertEqual(metadata.tags, ("nightly", "reporting"))
        self.assertEqual(dict(metadata.extra), {"k": "v"})

    def test_default_correlation_id_is_unique_per_instance(self):
        a = AutomationMetadata()
        b = AutomationMetadata()
        self.assertNotEqual(a.correlation_id, b.correlation_id)


class FieldOrderTests(unittest.TestCase):
    def test_field_order_places_extra_last(self):
        # This package's own literal field list is "created_at, owner,
        # correlation_id, version, tags, extra" - resolved by
        # following the now-established six-field order every prior
        # organizational-tier metadata module already uses instead:
        # created_at, version, correlation_id, owner, tags, extra. See
        # metadata.py's own module docstring.
        field_names = [f.name for f in dataclasses.fields(AutomationMetadata)]
        self.assertEqual(
            field_names,
            ["created_at", "version", "correlation_id", "owner", "tags", "extra"],
        )


class OwnerTests(unittest.TestCase):
    def test_owner_defaults_to_none(self):
        self.assertIsNone(AutomationMetadata().owner)

    def test_owner_accepts_a_string(self):
        self.assertEqual(AutomationMetadata(owner="Jane").owner, "Jane")


class TagsTests(unittest.TestCase):
    def test_tags_default_to_empty_tuple(self):
        self.assertEqual(AutomationMetadata().tags, ())

    def test_tags_are_wrapped_in_a_tuple_regardless_of_input_sequence_type(self):
        self.assertEqual(AutomationMetadata(tags=["a", "b"]).tags, ("a", "b"))
        self.assertEqual(AutomationMetadata(tags=("a", "b")).tags, ("a", "b"))

    def test_tags_defensive_copy_not_shared_with_caller(self):
        original = ["a", "b"]
        metadata = AutomationMetadata(tags=original)
        original.append("c")
        self.assertEqual(metadata.tags, ("a", "b"))


class ExtraTests(unittest.TestCase):
    def test_extra_is_wrapped_in_mappingproxytype(self):
        metadata = AutomationMetadata(extra={"a": 1})
        self.assertNotIsInstance(metadata.extra, dict)
        self.assertEqual(metadata.extra["a"], 1)

    def test_extra_defensive_copy_not_shared_with_caller(self):
        original = {"a": 1}
        metadata = AutomationMetadata(extra=original)
        original["a"] = 999
        self.assertEqual(metadata.extra["a"], 1)

    def test_extra_is_immutable(self):
        metadata = AutomationMetadata(extra={"a": 1})
        with self.assertRaises(TypeError):
            metadata.extra["a"] = 2


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        metadata = AutomationMetadata()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            metadata.version = "2.0"

    def test_tags_field_immutable(self):
        metadata = AutomationMetadata()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            metadata.tags = ("x",)


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        created_at = datetime(2026, 1, 1)
        a = AutomationMetadata(created_at=created_at, correlation_id="c1")
        b = AutomationMetadata(created_at=created_at, correlation_id="c1")
        self.assertEqual(a, b)

    def test_not_equal_when_correlation_id_differs(self):
        created_at = datetime(2026, 1, 1)
        a = AutomationMetadata(created_at=created_at, correlation_id="c1")
        b = AutomationMetadata(created_at=created_at, correlation_id="c2")
        self.assertNotEqual(a, b)

    def test_not_equal_when_owner_differs(self):
        created_at = datetime(2026, 1, 1)
        a = AutomationMetadata(created_at=created_at, correlation_id="c1", owner="Jane")
        b = AutomationMetadata(created_at=created_at, correlation_id="c1", owner="Bob")
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
