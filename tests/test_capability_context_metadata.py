"""Unit tests for
argus.capability_context.metadata.CapabilityContextMetadata."""

import dataclasses
import unittest
from datetime import datetime

from argus.capability_context import (
    CAPABILITY_CONTEXT_METADATA_VERSION,
    CapabilityContextMetadata,
)


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        metadata = CapabilityContextMetadata()
        self.assertIsInstance(metadata.created_at, datetime)
        self.assertEqual(metadata.version, CAPABILITY_CONTEXT_METADATA_VERSION)
        self.assertTrue(metadata.correlation_id)
        self.assertEqual(dict(metadata.extra), {})

    def test_all_fields_set(self):
        created_at = datetime(2026, 1, 1)
        metadata = CapabilityContextMetadata(
            created_at=created_at,
            version="9.9",
            correlation_id="fixed-id",
            extra={"k": "v"},
        )
        self.assertEqual(metadata.created_at, created_at)
        self.assertEqual(metadata.version, "9.9")
        self.assertEqual(metadata.correlation_id, "fixed-id")
        self.assertEqual(dict(metadata.extra), {"k": "v"})

    def test_default_correlation_id_is_unique_per_instance(self):
        a = CapabilityContextMetadata()
        b = CapabilityContextMetadata()
        self.assertNotEqual(a.correlation_id, b.correlation_id)


class StyleMirrorTests(unittest.TestCase):
    def test_field_set_mirrors_every_sibling_metadata_module(self):
        # This package's own work order lists "created_at,
        # correlation_id, version, extra" - a different relative
        # order than ContextMetadata/PlanningMetadata/TraceMetadata/
        # TaskMetadata/RelationshipMetadata/ExecutionMetadata/
        # CapabilityMetadata/CapabilityExecutionMetadata all use. This
        # package's own work order explicitly says "Follow existing
        # metadata conventions" - this module mirrors those eight's
        # shape and declared order instead - see metadata.py's own
        # module docstring.
        field_names = {f.name for f in dataclasses.fields(CapabilityContextMetadata)}
        self.assertEqual(field_names, {"created_at", "version", "correlation_id", "extra"})


class ExtraTests(unittest.TestCase):
    def test_extra_is_wrapped_in_mappingproxytype(self):
        metadata = CapabilityContextMetadata(extra={"a": 1})
        self.assertNotIsInstance(metadata.extra, dict)
        self.assertEqual(metadata.extra["a"], 1)

    def test_extra_defensive_copy_not_shared_with_caller(self):
        original = {"a": 1}
        metadata = CapabilityContextMetadata(extra=original)
        original["a"] = 999
        self.assertEqual(metadata.extra["a"], 1)

    def test_extra_is_immutable(self):
        metadata = CapabilityContextMetadata(extra={"a": 1})
        with self.assertRaises(TypeError):
            metadata.extra["a"] = 2


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        metadata = CapabilityContextMetadata()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            metadata.version = "2.0"


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        created_at = datetime(2026, 1, 1)
        a = CapabilityContextMetadata(created_at=created_at, correlation_id="c1")
        b = CapabilityContextMetadata(created_at=created_at, correlation_id="c1")
        self.assertEqual(a, b)

    def test_not_equal_when_correlation_id_differs(self):
        created_at = datetime(2026, 1, 1)
        a = CapabilityContextMetadata(created_at=created_at, correlation_id="c1")
        b = CapabilityContextMetadata(created_at=created_at, correlation_id="c2")
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
