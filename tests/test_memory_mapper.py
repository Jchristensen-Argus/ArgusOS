"""Unit tests for argus.memory_integration.mapper.MemoryMapper."""

import unittest

from argus.knowledge_graph import Entity
from argus.memory import MemoryRecord
from argus.memory_integration import InvalidMemoryRecordError, MemoryMapper


class MemoryMapperTestCase(unittest.TestCase):
    def setUp(self):
        self.mapper = MemoryMapper()

    def _record(self, **overrides):
        defaults = dict(key="alice", value={"name": "Alice"})
        defaults.update(overrides)
        return MemoryRecord(**defaults)


class MemoryToEntityTests(MemoryMapperTestCase):
    def test_translates_key_and_value(self):
        record = self._record()

        entity = self.mapper.memory_to_entity(record)

        self.assertEqual(entity.name, "alice")
        self.assertEqual(entity.entity_type, "memory")
        self.assertEqual(entity.attributes["value"], {"name": "Alice"})

    def test_entity_id_is_deterministic_from_key(self):
        record = self._record(key="bob")

        entity = self.mapper.memory_to_entity(record)

        self.assertEqual(entity.id, "memory:bob")

    def test_same_key_always_produces_same_entity_id(self):
        first = self.mapper.memory_to_entity(self._record(key="carol", value=1))
        second = self.mapper.memory_to_entity(self._record(key="carol", value=2))

        self.assertEqual(first.id, second.id)

    def test_attributes_include_memory_metadata(self):
        record = self._record()

        entity = self.mapper.memory_to_entity(record)

        self.assertEqual(entity.attributes["memory_id"], record.id)
        self.assertEqual(entity.attributes["version"], record.version)
        self.assertEqual(entity.attributes["created_at"], record.created_at)
        self.assertEqual(entity.attributes["updated_at"], record.updated_at)
        self.assertEqual(entity.attributes["expires_at"], record.expires_at)

    def test_rejects_non_memory_record(self):
        with self.assertRaises(InvalidMemoryRecordError):
            self.mapper.memory_to_entity("not-a-record")

    def test_rejects_empty_key(self):
        record = MemoryRecord(key="", value=1)

        with self.assertRaises(InvalidMemoryRecordError):
            self.mapper.memory_to_entity(record)


class MemoryToRelationshipTests(MemoryMapperTestCase):
    def test_no_relationships_when_value_is_not_a_mapping(self):
        record = self._record(value="just a string")

        self.assertEqual(self.mapper.memory_to_relationship(record), ())

    def test_no_relationships_when_related_keys_absent(self):
        record = self._record(value={"name": "Alice"})

        self.assertEqual(self.mapper.memory_to_relationship(record), ())

    def test_translates_related_keys_into_relationships(self):
        record = self._record(key="bob", value={"related_keys": ["alice"]})

        relationships = self.mapper.memory_to_relationship(record)

        self.assertEqual(len(relationships), 1)
        self.assertEqual(relationships[0].source_entity_id, "memory:bob")
        self.assertEqual(relationships[0].target_entity_id, "memory:alice")
        self.assertEqual(relationships[0].relationship_type, "related_to")

    def test_translates_multiple_related_keys(self):
        record = self._record(key="bob", value={"related_keys": ["alice", "carol"]})

        relationships = self.mapper.memory_to_relationship(record)

        targets = {r.target_entity_id for r in relationships}
        self.assertEqual(targets, {"memory:alice", "memory:carol"})

    def test_ignores_non_string_entries_in_related_keys(self):
        record = self._record(key="bob", value={"related_keys": ["alice", 123, None]})

        relationships = self.mapper.memory_to_relationship(record)

        self.assertEqual(len(relationships), 1)
        self.assertEqual(relationships[0].target_entity_id, "memory:alice")

    def test_related_keys_as_a_string_is_not_iterated_character_by_character(self):
        record = self._record(key="bob", value={"related_keys": "alice"})

        self.assertEqual(self.mapper.memory_to_relationship(record), ())

    def test_related_keys_not_iterable_is_ignored(self):
        record = self._record(key="bob", value={"related_keys": 42})

        self.assertEqual(self.mapper.memory_to_relationship(record), ())

    def test_rejects_non_memory_record(self):
        with self.assertRaises(InvalidMemoryRecordError):
            self.mapper.memory_to_relationship("not-a-record")


class UpdateEntityTests(MemoryMapperTestCase):
    def test_preserves_existing_id(self):
        existing = Entity(id="memory:alice", entity_type="memory", name="alice")
        record = self._record(value={"name": "Alice Updated"})

        updated = self.mapper.update_entity(existing, record)

        self.assertEqual(updated.id, existing.id)
        self.assertEqual(updated.attributes["value"], {"name": "Alice Updated"})

    def test_rejects_non_entity(self):
        record = self._record()

        with self.assertRaises(InvalidMemoryRecordError):
            self.mapper.update_entity("not-an-entity", record)

    def test_rejects_non_memory_record(self):
        existing = Entity(id="memory:alice", entity_type="memory", name="alice")

        with self.assertRaises(InvalidMemoryRecordError):
            self.mapper.update_entity(existing, "not-a-record")


class RemoveEntityTests(MemoryMapperTestCase):
    def test_returns_deterministic_entity_id(self):
        self.assertEqual(self.mapper.remove_entity("alice"), "memory:alice")

    def test_rejects_empty_key(self):
        with self.assertRaises(InvalidMemoryRecordError):
            self.mapper.remove_entity("")

    def test_rejects_non_string_key(self):
        with self.assertRaises(InvalidMemoryRecordError):
            self.mapper.remove_entity(123)


if __name__ == "__main__":
    unittest.main()
