"""Unit tests for argus.memory.storage.JSONMemoryStorage."""

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from argus.memory import MemoryRecord, MemoryServiceError
from argus.memory.storage import JSONMemoryStorage


class JSONMemoryStorageTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.path = Path(self._tmp_dir.name) / "memory_store.json"
        self.storage = JSONMemoryStorage(path=self.path)

    def test_load_returns_empty_list_when_file_does_not_exist(self):
        self.assertEqual(self.storage.load(), [])

    def test_save_then_load_round_trips_records(self):
        records = [
            MemoryRecord(key="a", value=1),
            MemoryRecord(key="b", value={"nested": True}),
        ]

        self.storage.save(records)
        loaded = self.storage.load()

        self.assertEqual(len(loaded), 2)
        loaded_by_key = {record.key: record for record in loaded}
        self.assertEqual(loaded_by_key["a"].value, 1)
        self.assertEqual(loaded_by_key["b"].value, {"nested": True})
        self.assertEqual(loaded_by_key["a"].id, records[0].id)

    def test_save_round_trips_expires_at(self):
        expires_at = datetime(2030, 1, 1, tzinfo=timezone.utc)
        self.storage.save([MemoryRecord(key="a", value=1, expires_at=expires_at)])

        loaded = self.storage.load()

        self.assertEqual(loaded[0].expires_at, expires_at)

    def test_save_round_trips_none_expires_at(self):
        self.storage.save([MemoryRecord(key="a", value=1)])

        loaded = self.storage.load()

        self.assertIsNone(loaded[0].expires_at)

    def test_save_creates_parent_directory_if_missing(self):
        nested_path = Path(self._tmp_dir.name) / "nested" / "store.json"
        storage = JSONMemoryStorage(path=nested_path)

        storage.save([MemoryRecord(key="a", value=1)])

        self.assertTrue(nested_path.exists())

    def test_save_writes_human_readable_json_array(self):
        self.storage.save([MemoryRecord(key="a", value=1)])

        with self.path.open("r", encoding="utf-8") as file:
            raw = json.load(file)

        self.assertIsInstance(raw, list)
        self.assertEqual(raw[0]["key"], "a")

    def test_save_leaves_no_temp_files_behind(self):
        self.storage.save([MemoryRecord(key="a", value=1)])

        leftovers = list(self.path.parent.glob("*.tmp"))
        self.assertEqual(leftovers, [])

    def test_save_overwrites_previous_contents(self):
        self.storage.save([MemoryRecord(key="a", value=1)])
        self.storage.save([MemoryRecord(key="b", value=2)])

        loaded = self.storage.load()

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].key, "b")

    def test_load_raises_memory_service_error_on_non_array_json(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"not": "a list"}), encoding="utf-8")

        with self.assertRaises(MemoryServiceError):
            self.storage.load()

    def test_load_raises_memory_service_error_on_malformed_json(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("{not valid json", encoding="utf-8")

        with self.assertRaises(MemoryServiceError):
            self.storage.load()

    def test_load_raises_memory_service_error_on_malformed_record(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([{"key": "a"}]), encoding="utf-8")

        with self.assertRaises(MemoryServiceError):
            self.storage.load()

    def test_default_path_is_memory_relative_path(self):
        storage = JSONMemoryStorage()

        self.assertEqual(storage._path, Path("memory/memory_store.json"))


if __name__ == "__main__":
    unittest.main()
