"""Unit tests for argus.knowledge.knowledge_record.KnowledgeRecord."""

import dataclasses
import unittest
import uuid
from datetime import datetime

from argus.knowledge import KnowledgeRecord


class KnowledgeRecordTests(unittest.TestCase):
    def test_stores_category_key_value(self):
        record = KnowledgeRecord(category="founder", key="name", value="Joel")

        self.assertEqual(record.category, "founder")
        self.assertEqual(record.key, "name")
        self.assertEqual(record.value, "Joel")

    def test_id_is_auto_generated_and_is_a_valid_uuid(self):
        record = KnowledgeRecord(category="founder", key="name", value="Joel")

        self.assertTrue(record.id)
        uuid.UUID(record.id)  # raises ValueError if not a valid UUID string

    def test_two_records_get_different_ids(self):
        first = KnowledgeRecord(category="c", key="a", value=1)
        second = KnowledgeRecord(category="c", key="b", value=2)

        self.assertNotEqual(first.id, second.id)

    def test_created_at_and_updated_at_are_auto_generated_datetimes(self):
        record = KnowledgeRecord(category="c", key="a", value=1)

        self.assertIsInstance(record.created_at, datetime)
        self.assertIsInstance(record.updated_at, datetime)

    def test_version_defaults_to_one(self):
        record = KnowledgeRecord(category="c", key="a", value=1)

        self.assertEqual(record.version, 1)

    def test_explicit_fields_are_honored(self):
        record = KnowledgeRecord(
            category="c",
            key="a",
            value=1,
            id="fixed-id",
            version=7,
        )

        self.assertEqual(record.id, "fixed-id")
        self.assertEqual(record.version, 7)

    def test_record_is_immutable(self):
        record = KnowledgeRecord(category="c", key="a", value=1)

        with self.assertRaises(dataclasses.FrozenInstanceError):
            record.value = 2

    def test_replace_produces_a_new_record_without_mutating_the_original(self):
        original = KnowledgeRecord(category="c", key="a", value=1)

        updated = dataclasses.replace(original, value=2, version=2)

        self.assertEqual(original.value, 1)
        self.assertEqual(original.version, 1)
        self.assertEqual(updated.value, 2)
        self.assertEqual(updated.version, 2)
        self.assertEqual(updated.id, original.id)


if __name__ == "__main__":
    unittest.main()
