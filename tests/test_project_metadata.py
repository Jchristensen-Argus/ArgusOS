"""Unit tests for argus.project.metadata.ProjectMetadata."""

import dataclasses
import unittest
from datetime import datetime

from argus.project import PROJECT_METADATA_VERSION, ProjectMetadata


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        metadata = ProjectMetadata()
        self.assertIsInstance(metadata.created_at, datetime)
        self.assertEqual(metadata.version, PROJECT_METADATA_VERSION)
        self.assertTrue(metadata.correlation_id)
        self.assertIsNone(metadata.owner)
        self.assertEqual(metadata.tags, ())
        self.assertEqual(dict(metadata.extra), {})

    def test_all_fields_set(self):
        created_at = datetime(2026, 1, 1)
        metadata = ProjectMetadata(
            created_at=created_at,
            version="9.9",
            correlation_id="fixed-id",
            owner="Jane",
            tags=["soap", "retail"],
            extra={"k": "v"},
        )
        self.assertEqual(metadata.created_at, created_at)
        self.assertEqual(metadata.version, "9.9")
        self.assertEqual(metadata.correlation_id, "fixed-id")
        self.assertEqual(metadata.owner, "Jane")
        self.assertEqual(metadata.tags, ("soap", "retail"))
        self.assertEqual(dict(metadata.extra), {"k": "v"})

    def test_default_correlation_id_is_unique_per_instance(self):
        a = ProjectMetadata()
        b = ProjectMetadata()
        self.assertNotEqual(a.correlation_id, b.correlation_id)


class FieldOrderTests(unittest.TestCase):
    def test_field_order_places_extra_last(self):
        # This package's own "Suggested fields" list omits
        # correlation_id and adds owner/tags - resolved by keeping
        # the established quartet's own relative order
        # (created_at, version, correlation_id) and appending the new
        # domain-specific fields (owner, tags) before extra, which
        # stays last per every metadata module's own convention. See
        # metadata.py's own module docstring.
        field_names = [f.name for f in dataclasses.fields(ProjectMetadata)]
        self.assertEqual(
            field_names,
            ["created_at", "version", "correlation_id", "owner", "tags", "extra"],
        )


class OwnerTests(unittest.TestCase):
    def test_owner_defaults_to_none(self):
        self.assertIsNone(ProjectMetadata().owner)

    def test_owner_accepts_a_string(self):
        self.assertEqual(ProjectMetadata(owner="Jane").owner, "Jane")


class TagsTests(unittest.TestCase):
    def test_tags_default_to_empty_tuple(self):
        self.assertEqual(ProjectMetadata().tags, ())

    def test_tags_are_wrapped_in_a_tuple_regardless_of_input_sequence_type(self):
        self.assertEqual(ProjectMetadata(tags=["a", "b"]).tags, ("a", "b"))
        self.assertEqual(ProjectMetadata(tags=("a", "b")).tags, ("a", "b"))

    def test_tags_defensive_copy_not_shared_with_caller(self):
        original = ["a", "b"]
        metadata = ProjectMetadata(tags=original)
        original.append("c")
        self.assertEqual(metadata.tags, ("a", "b"))


class ExtraTests(unittest.TestCase):
    def test_extra_is_wrapped_in_mappingproxytype(self):
        metadata = ProjectMetadata(extra={"a": 1})
        self.assertNotIsInstance(metadata.extra, dict)
        self.assertEqual(metadata.extra["a"], 1)

    def test_extra_defensive_copy_not_shared_with_caller(self):
        original = {"a": 1}
        metadata = ProjectMetadata(extra=original)
        original["a"] = 999
        self.assertEqual(metadata.extra["a"], 1)

    def test_extra_is_immutable(self):
        metadata = ProjectMetadata(extra={"a": 1})
        with self.assertRaises(TypeError):
            metadata.extra["a"] = 2


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        metadata = ProjectMetadata()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            metadata.version = "2.0"

    def test_tags_field_immutable(self):
        metadata = ProjectMetadata()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            metadata.tags = ("x",)


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        created_at = datetime(2026, 1, 1)
        a = ProjectMetadata(created_at=created_at, correlation_id="c1")
        b = ProjectMetadata(created_at=created_at, correlation_id="c1")
        self.assertEqual(a, b)

    def test_not_equal_when_correlation_id_differs(self):
        created_at = datetime(2026, 1, 1)
        a = ProjectMetadata(created_at=created_at, correlation_id="c1")
        b = ProjectMetadata(created_at=created_at, correlation_id="c2")
        self.assertNotEqual(a, b)

    def test_not_equal_when_owner_differs(self):
        created_at = datetime(2026, 1, 1)
        a = ProjectMetadata(created_at=created_at, correlation_id="c1", owner="Jane")
        b = ProjectMetadata(created_at=created_at, correlation_id="c1", owner="Bob")
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
