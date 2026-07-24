"""Unit tests for argus.knowledge.storage.JSONKnowledgeStorage."""

import json
import tempfile
import unittest
from pathlib import Path

from argus.knowledge import KnowledgeError, KnowledgeRecord
from argus.knowledge.storage import JSONKnowledgeStorage


class JSONKnowledgeStorageTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.base_dir = Path(self._tmp_dir.name)
        self.storage = JSONKnowledgeStorage(base_dir=self.base_dir)

    def test_list_categories_empty_when_directory_does_not_exist(self):
        missing_dir = self.base_dir / "does_not_exist"
        storage = JSONKnowledgeStorage(base_dir=missing_dir)

        self.assertEqual(storage.list_categories(), [])

    def test_load_unknown_category_returns_empty_list(self):
        self.assertEqual(self.storage.load("founder"), [])

    def test_save_then_load_round_trips_records(self):
        records = [
            KnowledgeRecord(category="founder", key="name", value="Joel"),
            KnowledgeRecord(category="founder", key="role", value="Founder"),
        ]

        self.storage.save("founder", records)
        loaded = self.storage.load("founder")

        self.assertEqual(len(loaded), 2)
        loaded_by_key = {record.key: record for record in loaded}
        self.assertEqual(loaded_by_key["name"].value, "Joel")
        self.assertEqual(loaded_by_key["role"].value, "Founder")
        self.assertEqual(loaded_by_key["name"].id, records[0].id)

    def test_save_creates_base_directory_if_missing(self):
        nested_dir = self.base_dir / "nested"
        storage = JSONKnowledgeStorage(base_dir=nested_dir)

        storage.save("founder", [KnowledgeRecord(category="founder", key="a", value=1)])

        self.assertTrue((nested_dir / "founder.json").exists())

    def test_save_writes_human_readable_json_array(self):
        self.storage.save(
            "founder", [KnowledgeRecord(category="founder", key="a", value=1)]
        )

        path = self.base_dir / "founder.json"
        with path.open("r", encoding="utf-8") as file:
            raw = json.load(file)

        self.assertIsInstance(raw, list)
        self.assertEqual(len(raw), 1)
        self.assertEqual(raw[0]["key"], "a")

    def test_save_leaves_no_temp_files_behind(self):
        self.storage.save(
            "founder", [KnowledgeRecord(category="founder", key="a", value=1)]
        )

        leftovers = list(self.base_dir.glob("*.tmp"))
        self.assertEqual(leftovers, [])

    def test_save_overwrites_previous_contents_of_the_category(self):
        self.storage.save("founder", [KnowledgeRecord(category="founder", key="a", value=1)])
        self.storage.save("founder", [KnowledgeRecord(category="founder", key="b", value=2)])

        loaded = self.storage.load("founder")

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].key, "b")

    def test_list_categories_reflects_saved_files(self):
        self.storage.save("founder", [])
        self.storage.save("architecture", [])

        self.assertEqual(self.storage.list_categories(), ["architecture", "founder"])

    def test_load_raises_knowledge_error_on_non_array_json(self):
        path = self.base_dir / "founder.json"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"not": "a list"}), encoding="utf-8")

        with self.assertRaises(KnowledgeError):
            self.storage.load("founder")

    def test_load_raises_knowledge_error_on_malformed_json(self):
        path = self.base_dir / "founder.json"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        path.write_text("{not valid json", encoding="utf-8")

        with self.assertRaises(KnowledgeError):
            self.storage.load("founder")

    def test_load_raises_knowledge_error_on_malformed_record(self):
        path = self.base_dir / "founder.json"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps([{"key": "a"}]), encoding="utf-8")

        with self.assertRaises(KnowledgeError):
            self.storage.load("founder")

    def test_default_base_dir_is_knowledge_relative_path(self):
        storage = JSONKnowledgeStorage()

        self.assertEqual(storage._path_for("founder"), Path("knowledge/founder.json"))


if __name__ == "__main__":
    unittest.main()
