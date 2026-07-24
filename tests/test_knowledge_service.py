"""Unit tests for argus.knowledge.knowledge_service.KnowledgeService."""

import logging
import tempfile
import unittest
from pathlib import Path

from argus.events import EventType, InMemoryEventBus
from argus.knowledge import (
    DuplicateKnowledgeError,
    KnowledgeError,
    KnowledgeNotFoundError,
    KnowledgeRecord,
    KnowledgeService,
)
from argus.knowledge.storage import JSONKnowledgeStorage


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_knowledge_service")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


class KnowledgeServiceTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.base_dir = Path(self._tmp_dir.name)
        self.event_bus = InMemoryEventBus(logger=_silent_logger())

    def _new_service(self) -> KnowledgeService:
        storage = JSONKnowledgeStorage(base_dir=self.base_dir)
        return KnowledgeService(storage=storage, event_bus=self.event_bus)

    def test_put_then_get_round_trips(self):
        service = self._new_service()
        record = KnowledgeRecord(category="founder", key="name", value="Joel")

        service.put(record)

        self.assertEqual(service.get("name"), record)

    def test_put_duplicate_key_raises(self):
        service = self._new_service()
        service.put(KnowledgeRecord(category="founder", key="name", value="Joel"))

        with self.assertRaises(DuplicateKnowledgeError):
            service.put(KnowledgeRecord(category="founder", key="name", value="Someone Else"))

    def test_put_rejects_non_record(self):
        service = self._new_service()

        with self.assertRaises(KnowledgeError):
            service.put({"key": "name", "value": "Joel"})

    def test_put_rejects_empty_key(self):
        service = self._new_service()

        with self.assertRaises(KnowledgeError):
            service.put(KnowledgeRecord(category="founder", key="", value="Joel"))

    def test_put_rejects_empty_category(self):
        service = self._new_service()

        with self.assertRaises(KnowledgeError):
            service.put(KnowledgeRecord(category="", key="name", value="Joel"))

    def test_get_missing_key_raises_not_found(self):
        service = self._new_service()

        with self.assertRaises(KnowledgeNotFoundError):
            service.get("does-not-exist")

    def test_exists_true_and_false(self):
        service = self._new_service()
        service.put(KnowledgeRecord(category="founder", key="name", value="Joel"))

        self.assertTrue(service.exists("name"))
        self.assertFalse(service.exists("nope"))

    def test_delete_removes_record(self):
        service = self._new_service()
        service.put(KnowledgeRecord(category="founder", key="name", value="Joel"))

        service.delete("name")

        self.assertFalse(service.exists("name"))

    def test_delete_missing_key_raises_not_found(self):
        service = self._new_service()

        with self.assertRaises(KnowledgeNotFoundError):
            service.delete("does-not-exist")

    def test_update_missing_key_raises_not_found(self):
        service = self._new_service()

        with self.assertRaises(KnowledgeNotFoundError):
            service.update("does-not-exist", "value")

    def test_update_bumps_version_and_changes_value(self):
        service = self._new_service()
        service.put(KnowledgeRecord(category="founder", key="name", value="Joel"))

        updated = service.update("name", "Joel Christensen")

        self.assertEqual(updated.value, "Joel Christensen")
        self.assertEqual(updated.version, 2)
        self.assertEqual(service.get("name").version, 2)

    def test_update_bumps_updated_at(self):
        service = self._new_service()
        service.put(KnowledgeRecord(category="founder", key="name", value="Joel"))
        original_updated_at = service.get("name").updated_at

        updated = service.update("name", "Joel Christensen")

        self.assertGreaterEqual(updated.updated_at, original_updated_at)

    def test_list_returns_all_records(self):
        service = self._new_service()
        service.put(KnowledgeRecord(category="founder", key="a", value=1))
        service.put(KnowledgeRecord(category="businesses", key="b", value=2))

        records = service.list()

        self.assertEqual({record.key for record in records}, {"a", "b"})

    def test_list_filters_by_category(self):
        service = self._new_service()
        service.put(KnowledgeRecord(category="founder", key="a", value=1))
        service.put(KnowledgeRecord(category="businesses", key="b", value=2))

        founder_records = service.list(category="founder")

        self.assertEqual([record.key for record in founder_records], ["a"])

    def test_put_publishes_knowledge_created_event(self):
        service = self._new_service()
        received = []
        self.event_bus.subscribe(EventType.KNOWLEDGE_CREATED, received.append)

        service.put(KnowledgeRecord(category="founder", key="a", value=1))

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].payload["key"], "a")
        self.assertEqual(received[0].payload["category"], "founder")
        self.assertEqual(received[0].source, "knowledge_service")

    def test_update_publishes_knowledge_updated_event(self):
        service = self._new_service()
        service.put(KnowledgeRecord(category="founder", key="a", value=1))
        received = []
        self.event_bus.subscribe(EventType.KNOWLEDGE_UPDATED, received.append)

        service.update("a", 2)

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].payload["version"], 2)

    def test_delete_publishes_knowledge_deleted_event(self):
        service = self._new_service()
        service.put(KnowledgeRecord(category="founder", key="a", value=1))
        received = []
        self.event_bus.subscribe(EventType.KNOWLEDGE_DELETED, received.append)

        service.delete("a")

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].payload["key"], "a")

    def test_data_persists_across_service_instances(self):
        first = self._new_service()
        first.put(KnowledgeRecord(category="founder", key="name", value="Joel"))

        second = self._new_service()

        self.assertTrue(second.exists("name"))
        self.assertEqual(second.get("name").value, "Joel")

    def test_delete_persists_across_service_instances(self):
        first = self._new_service()
        first.put(KnowledgeRecord(category="founder", key="name", value="Joel"))
        first.delete("name")

        second = self._new_service()

        self.assertFalse(second.exists("name"))

    def test_constructing_service_loads_existing_storage_contents(self):
        storage = JSONKnowledgeStorage(base_dir=self.base_dir)
        storage.save(
            "founder",
            [KnowledgeRecord(category="founder", key="preexisting", value="already here")],
        )

        service = KnowledgeService(storage=storage, event_bus=self.event_bus)

        self.assertTrue(service.exists("preexisting"))


if __name__ == "__main__":
    unittest.main()
