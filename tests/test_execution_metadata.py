"""Unit tests for argus.execution_engine.metadata.ExecutionMetadata."""

import dataclasses
import unittest
from datetime import datetime

from argus.execution_engine import EXECUTION_METADATA_VERSION, ExecutionMetadata


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        metadata = ExecutionMetadata()
        self.assertIsInstance(metadata.created_at, datetime)
        self.assertEqual(metadata.version, EXECUTION_METADATA_VERSION)
        self.assertTrue(metadata.correlation_id)
        self.assertEqual(dict(metadata.extra), {})

    def test_all_fields_set(self):
        created_at = datetime(2026, 1, 1)
        metadata = ExecutionMetadata(
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
        a = ExecutionMetadata()
        b = ExecutionMetadata()
        self.assertNotEqual(a.correlation_id, b.correlation_id)


class StyleMirrorTests(unittest.TestCase):
    def test_field_set_mirrors_context_planning_trace_task_and_relationship_metadata(self):
        # This package's own work order lists "created_at,
        # correlation_id, version, extra" - a different relative
        # order than ContextMetadata/PlanningMetadata/TraceMetadata/
        # TaskMetadata/RelationshipMetadata all use. This module
        # mirrors those five's shape and declared order instead - see
        # metadata.py's own module docstring.
        field_names = {f.name for f in dataclasses.fields(ExecutionMetadata)}
        self.assertEqual(field_names, {"created_at", "version", "correlation_id", "extra"})


class ExtraTests(unittest.TestCase):
    def test_extra_is_wrapped_in_mappingproxytype(self):
        metadata = ExecutionMetadata(extra={"a": 1})
        self.assertNotIsInstance(metadata.extra, dict)
        self.assertEqual(metadata.extra["a"], 1)

    def test_extra_defensive_copy_not_shared_with_caller(self):
        original = {"a": 1}
        metadata = ExecutionMetadata(extra=original)
        original["a"] = 999
        self.assertEqual(metadata.extra["a"], 1)

    def test_extra_is_immutable(self):
        metadata = ExecutionMetadata(extra={"a": 1})
        with self.assertRaises(TypeError):
            metadata.extra["a"] = 2


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        metadata = ExecutionMetadata()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            metadata.version = "2.0"


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        created_at = datetime(2026, 1, 1)
        a = ExecutionMetadata(created_at=created_at, correlation_id="c1")
        b = ExecutionMetadata(created_at=created_at, correlation_id="c1")
        self.assertEqual(a, b)

    def test_not_equal_when_correlation_id_differs(self):
        created_at = datetime(2026, 1, 1)
        a = ExecutionMetadata(created_at=created_at, correlation_id="c1")
        b = ExecutionMetadata(created_at=created_at, correlation_id="c2")
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
