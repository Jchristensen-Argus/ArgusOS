"""Unit tests for argus.response.metadata.ResponseMetadata."""

import dataclasses
import unittest
from datetime import datetime

from argus.response import ResponseMetadata
from argus.response.metadata import RESPONSE_METADATA_VERSION


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        metadata = ResponseMetadata()
        self.assertIsInstance(metadata.timestamp, datetime)
        self.assertEqual(metadata.version, RESPONSE_METADATA_VERSION)
        self.assertTrue(metadata.correlation_id)
        self.assertEqual(dict(metadata.extra), {})

    def test_all_fields_set(self):
        timestamp = datetime(2026, 1, 1)
        metadata = ResponseMetadata(
            timestamp=timestamp,
            version="2.0",
            correlation_id="fixed-id",
            extra={"k": "v"},
        )
        self.assertEqual(metadata.timestamp, timestamp)
        self.assertEqual(metadata.version, "2.0")
        self.assertEqual(metadata.correlation_id, "fixed-id")
        self.assertEqual(dict(metadata.extra), {"k": "v"})

    def test_default_correlation_id_is_unique_per_instance(self):
        a = ResponseMetadata()
        b = ResponseMetadata()
        self.assertNotEqual(a.correlation_id, b.correlation_id)


class ExtraTests(unittest.TestCase):
    def test_extra_is_wrapped_in_mappingproxytype(self):
        metadata = ResponseMetadata(extra={"a": 1})
        self.assertNotIsInstance(metadata.extra, dict)
        self.assertEqual(metadata.extra["a"], 1)

    def test_extra_defensive_copy_not_shared_with_caller(self):
        original = {"a": 1}
        metadata = ResponseMetadata(extra=original)
        original["a"] = 999
        self.assertEqual(metadata.extra["a"], 1)

    def test_extra_is_immutable(self):
        metadata = ResponseMetadata(extra={"a": 1})
        with self.assertRaises(TypeError):
            metadata.extra["a"] = 2


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        metadata = ResponseMetadata()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            metadata.version = "changed"


class StyleMirrorTests(unittest.TestCase):
    def test_field_names_mirror_context_and_planning_metadata_shape(self):
        # Mirrors ContextMetadata/PlanningMetadata's shape, with the
        # one explicit "timestamp" (not "created_at") field-name
        # deviation this package's own work order specifies.
        field_names = {f.name for f in dataclasses.fields(ResponseMetadata)}
        self.assertEqual(field_names, {"timestamp", "version", "correlation_id", "extra"})


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        timestamp = datetime(2026, 1, 1)
        a = ResponseMetadata(
            timestamp=timestamp, version="1.0", correlation_id="c1", extra={"k": "v"}
        )
        b = ResponseMetadata(
            timestamp=timestamp, version="1.0", correlation_id="c1", extra={"k": "v"}
        )
        self.assertEqual(a, b)

    def test_two_default_constructed_instances_are_not_equal(self):
        a = ResponseMetadata()
        b = ResponseMetadata()
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
