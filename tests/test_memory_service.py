"""Unit tests for argus.memory.memory_service.MemoryService."""

import logging
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from argus.events import EventType, InMemoryEventBus
from argus.memory import (
    DuplicateMemoryError,
    MemoryNotFoundError,
    MemoryRecord,
    MemoryService,
    MemoryServiceError,
)
from argus.memory.storage import JSONMemoryStorage


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_memory_service")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


class MemoryServiceTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.path = Path(self._tmp_dir.name) / "memory_store.json"
        self.event_bus = InMemoryEventBus(logger=_silent_logger())

    def _new_service(self) -> MemoryService:
        storage = JSONMemoryStorage(path=self.path)
        return MemoryService(storage=storage, event_bus=self.event_bus)

    def _expired_record(self, key: str, value=1) -> MemoryRecord:
        return MemoryRecord(
            key=key, value=value, expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)
        )

    # -- put / get / exists --------------------------------------------

    def test_put_then_get_round_trips(self):
        service = self._new_service()
        record = MemoryRecord(key="a", value=1)

        service.put(record)

        self.assertEqual(service.get("a"), record)

    def test_put_duplicate_key_raises(self):
        service = self._new_service()
        service.put(MemoryRecord(key="a", value=1))

        with self.assertRaises(DuplicateMemoryError):
            service.put(MemoryRecord(key="a", value=2))

    def test_put_duplicate_key_raises_even_if_existing_record_is_expired(self):
        service = self._new_service()
        service.put(self._expired_record("a"))

        with self.assertRaises(DuplicateMemoryError):
            service.put(MemoryRecord(key="a", value=2))

    def test_put_rejects_non_record(self):
        service = self._new_service()

        with self.assertRaises(MemoryServiceError):
            service.put({"key": "a", "value": 1})

    def test_put_rejects_empty_key(self):
        service = self._new_service()

        with self.assertRaises(MemoryServiceError):
            service.put(MemoryRecord(key="", value=1))

    def test_get_missing_key_raises_not_found(self):
        service = self._new_service()

        with self.assertRaises(MemoryNotFoundError):
            service.get("missing")

    def test_get_expired_key_raises_not_found(self):
        service = self._new_service()
        service.put(self._expired_record("a"))

        with self.assertRaises(MemoryNotFoundError):
            service.get("a")

    def test_exists_true_and_false(self):
        service = self._new_service()
        service.put(MemoryRecord(key="a", value=1))

        self.assertTrue(service.exists("a"))
        self.assertFalse(service.exists("nope"))

    def test_exists_false_for_expired_record(self):
        service = self._new_service()
        service.put(self._expired_record("a"))

        self.assertFalse(service.exists("a"))

    # -- delete -----------------------------------------------------------

    def test_delete_removes_record(self):
        service = self._new_service()
        service.put(MemoryRecord(key="a", value=1))

        service.delete("a")

        self.assertFalse(service.exists("a"))

    def test_delete_missing_key_raises_not_found(self):
        service = self._new_service()

        with self.assertRaises(MemoryNotFoundError):
            service.delete("missing")

    def test_delete_expired_key_raises_not_found(self):
        service = self._new_service()
        service.put(self._expired_record("a"))

        with self.assertRaises(MemoryNotFoundError):
            service.delete("a")

    # -- update -------------------------------------------------------

    def test_update_missing_key_raises_not_found(self):
        service = self._new_service()

        with self.assertRaises(MemoryNotFoundError):
            service.update("missing", "value")

    def test_update_bumps_version_and_changes_value(self):
        service = self._new_service()
        service.put(MemoryRecord(key="a", value=1))

        updated = service.update("a", 2)

        self.assertEqual(updated.value, 2)
        self.assertEqual(updated.version, 2)
        self.assertEqual(service.get("a").version, 2)

    def test_update_expired_key_raises_not_found(self):
        service = self._new_service()
        service.put(self._expired_record("a"))

        with self.assertRaises(MemoryNotFoundError):
            service.update("a", 2)

    # -- list / search --------------------------------------------------

    def test_list_returns_all_non_expired_records(self):
        service = self._new_service()
        service.put(MemoryRecord(key="a", value=1))
        service.put(self._expired_record("b"))

        self.assertEqual([record.key for record in service.list()], ["a"])

    def test_search_matches_substring_case_insensitively(self):
        service = self._new_service()
        service.put(MemoryRecord(key="Founder.Name", value="Joel"))
        service.put(MemoryRecord(key="business.status", value="active"))

        results = service.search("founder")

        self.assertEqual([record.key for record in results], ["Founder.Name"])

    def test_search_excludes_expired_records(self):
        service = self._new_service()
        service.put(self._expired_record("founder.name"))

        self.assertEqual(service.search("founder"), ())

    # -- purge_expired ----------------------------------------------------

    def test_purge_expired_removes_only_expired_records(self):
        service = self._new_service()
        service.put(MemoryRecord(key="a", value=1))
        service.put(self._expired_record("b"))

        purged_count = service.purge_expired()

        self.assertEqual(purged_count, 1)
        self.assertTrue(service.exists("a"))
        self.assertFalse(service.exists("b"))

    def test_purge_expired_allows_key_reuse(self):
        service = self._new_service()
        service.put(self._expired_record("a"))
        service.purge_expired()

        service.put(MemoryRecord(key="a", value="new"))

        self.assertEqual(service.get("a").value, "new")

    def test_purge_expired_returns_zero_when_nothing_expired(self):
        service = self._new_service()
        service.put(MemoryRecord(key="a", value=1))

        self.assertEqual(service.purge_expired(), 0)

    # -- events -----------------------------------------------------------

    def test_put_publishes_memory_updated_event_with_created_operation(self):
        service = self._new_service()
        received = []
        self.event_bus.subscribe(EventType.MEMORY_UPDATED, received.append)

        service.put(MemoryRecord(key="a", value=1))

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].payload["operation"], "created")
        self.assertEqual(received[0].payload["key"], "a")
        self.assertEqual(received[0].source, "memory_service")

    def test_update_publishes_memory_updated_event_with_updated_operation(self):
        service = self._new_service()
        service.put(MemoryRecord(key="a", value=1))
        received = []
        self.event_bus.subscribe(EventType.MEMORY_UPDATED, received.append)

        service.update("a", 2)

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].payload["operation"], "updated")

    def test_delete_publishes_memory_updated_event_with_deleted_operation(self):
        service = self._new_service()
        service.put(MemoryRecord(key="a", value=1))
        received = []
        self.event_bus.subscribe(EventType.MEMORY_UPDATED, received.append)

        service.delete("a")

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].payload["operation"], "deleted")

    def test_purge_expired_publishes_memory_updated_event_with_purged_operation(self):
        service = self._new_service()
        service.put(self._expired_record("a"))
        received = []
        self.event_bus.subscribe(EventType.MEMORY_UPDATED, received.append)

        service.purge_expired()

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].payload["operation"], "purged")

    def test_purge_expired_with_nothing_expired_publishes_no_event(self):
        service = self._new_service()
        service.put(MemoryRecord(key="a", value=1))
        received = []
        self.event_bus.subscribe(EventType.MEMORY_UPDATED, received.append)

        service.purge_expired()

        self.assertEqual(received, [])

    # -- persistence ------------------------------------------------------

    def test_data_persists_across_service_instances(self):
        first = self._new_service()
        first.put(MemoryRecord(key="a", value=1))

        second = self._new_service()

        self.assertTrue(second.exists("a"))
        self.assertEqual(second.get("a").value, 1)

    def test_delete_persists_across_service_instances(self):
        first = self._new_service()
        first.put(MemoryRecord(key="a", value=1))
        first.delete("a")

        second = self._new_service()

        self.assertFalse(second.exists("a"))

    def test_constructing_service_loads_existing_storage_contents(self):
        storage = JSONMemoryStorage(path=self.path)
        storage.save([MemoryRecord(key="preexisting", value="already here")])

        service = MemoryService(storage=storage, event_bus=self.event_bus)

        self.assertTrue(service.exists("preexisting"))

    def test_expired_records_remain_on_disk_until_purged(self):
        first = self._new_service()
        first.put(self._expired_record("a"))

        storage = JSONMemoryStorage(path=self.path)
        raw_records = storage.load()

        self.assertEqual(len(raw_records), 1)
        self.assertEqual(raw_records[0].key, "a")


if __name__ == "__main__":
    unittest.main()
