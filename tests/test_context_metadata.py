"""Unit tests for argus.context.metadata.ContextMetadata."""

import dataclasses
import unittest
from datetime import datetime, timezone
from types import MappingProxyType

from argus.context.metadata import CONTEXT_METADATA_VERSION, ContextMetadata


class ContextMetadataTests(unittest.TestCase):
    def test_defaults(self):
        metadata = ContextMetadata()
        self.assertIsInstance(metadata.created_at, datetime)
        self.assertEqual(metadata.version, CONTEXT_METADATA_VERSION)
        self.assertTrue(metadata.correlation_id)
        self.assertIsInstance(metadata.correlation_id, str)
        self.assertEqual(dict(metadata.extra), {})

    def test_all_fields_set(self):
        created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        metadata = ContextMetadata(
            created_at=created_at,
            version="2.0",
            correlation_id="corr-1",
            extra={"foo": "bar"},
        )
        self.assertEqual(metadata.created_at, created_at)
        self.assertEqual(metadata.version, "2.0")
        self.assertEqual(metadata.correlation_id, "corr-1")
        self.assertEqual(dict(metadata.extra), {"foo": "bar"})

    def test_default_correlation_id_is_unique_per_instance(self):
        first = ContextMetadata()
        second = ContextMetadata()
        self.assertNotEqual(first.correlation_id, second.correlation_id)

    def test_extra_is_wrapped_in_mappingproxytype(self):
        metadata = ContextMetadata(extra={"a": 1})
        self.assertIsInstance(metadata.extra, MappingProxyType)

    def test_extra_defensive_copy_not_shared_with_caller(self):
        source = {"a": 1}
        metadata = ContextMetadata(extra=source)
        source["a"] = 999
        source["b"] = 2
        self.assertEqual(dict(metadata.extra), {"a": 1})

    def test_extra_is_immutable(self):
        metadata = ContextMetadata(extra={"a": 1})
        with self.assertRaises(TypeError):
            metadata.extra["a"] = 2

    def test_immutability(self):
        metadata = ContextMetadata()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            metadata.version = "9.9"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            metadata.created_at = datetime.now(timezone.utc)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            metadata.correlation_id = "changed"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            metadata.extra = {}

    def test_equality_when_all_fields_match(self):
        created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        first = ContextMetadata(created_at=created_at, correlation_id="x", extra={"a": 1})
        second = ContextMetadata(created_at=created_at, correlation_id="x", extra={"a": 1})
        self.assertEqual(first, second)

    def test_inequality_by_correlation_id(self):
        created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        first = ContextMetadata(created_at=created_at, correlation_id="x")
        second = ContextMetadata(created_at=created_at, correlation_id="y")
        self.assertNotEqual(first, second)

    def test_inequality_by_extra(self):
        created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        first = ContextMetadata(created_at=created_at, correlation_id="x", extra={"a": 1})
        second = ContextMetadata(created_at=created_at, correlation_id="x", extra={"a": 2})
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
