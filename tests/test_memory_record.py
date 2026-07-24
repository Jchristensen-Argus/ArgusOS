"""Unit tests for argus.memory.memory_record.MemoryRecord."""

import dataclasses
import unittest
import uuid
from datetime import datetime, timedelta, timezone

from argus.memory import MemoryRecord


class MemoryRecordTests(unittest.TestCase):
    def test_stores_key_and_value(self):
        record = MemoryRecord(key="a", value=1)

        self.assertEqual(record.key, "a")
        self.assertEqual(record.value, 1)

    def test_id_is_auto_generated_and_is_a_valid_uuid(self):
        record = MemoryRecord(key="a", value=1)

        self.assertTrue(record.id)
        uuid.UUID(record.id)

    def test_two_records_get_different_ids(self):
        first = MemoryRecord(key="a", value=1)
        second = MemoryRecord(key="b", value=2)

        self.assertNotEqual(first.id, second.id)

    def test_created_at_and_updated_at_are_auto_generated_datetimes(self):
        record = MemoryRecord(key="a", value=1)

        self.assertIsInstance(record.created_at, datetime)
        self.assertIsInstance(record.updated_at, datetime)

    def test_expires_at_defaults_to_none(self):
        record = MemoryRecord(key="a", value=1)

        self.assertIsNone(record.expires_at)

    def test_version_defaults_to_one(self):
        record = MemoryRecord(key="a", value=1)

        self.assertEqual(record.version, 1)

    def test_record_is_immutable(self):
        record = MemoryRecord(key="a", value=1)

        with self.assertRaises(dataclasses.FrozenInstanceError):
            record.value = 2

    def test_replace_produces_a_new_record_without_mutating_the_original(self):
        original = MemoryRecord(key="a", value=1)

        updated = dataclasses.replace(original, value=2, version=2)

        self.assertEqual(original.value, 1)
        self.assertEqual(updated.value, 2)
        self.assertEqual(updated.id, original.id)

    def test_is_expired_false_when_expires_at_is_none(self):
        record = MemoryRecord(key="a", value=1)

        self.assertFalse(record.is_expired())

    def test_is_expired_false_when_expires_at_is_in_the_future(self):
        record = MemoryRecord(
            key="a", value=1, expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        self.assertFalse(record.is_expired())

    def test_is_expired_true_when_expires_at_is_in_the_past(self):
        record = MemoryRecord(
            key="a", value=1, expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)
        )

        self.assertTrue(record.is_expired())

    def test_is_expired_true_when_expires_at_equals_now(self):
        now = datetime.now(timezone.utc)
        record = MemoryRecord(key="a", value=1, expires_at=now)

        self.assertTrue(record.is_expired(now=now))

    def test_is_expired_accepts_explicit_now(self):
        expires_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        record = MemoryRecord(key="a", value=1, expires_at=expires_at)

        self.assertFalse(record.is_expired(now=datetime(2025, 12, 31, tzinfo=timezone.utc)))
        self.assertTrue(record.is_expired(now=datetime(2026, 1, 2, tzinfo=timezone.utc)))


if __name__ == "__main__":
    unittest.main()
