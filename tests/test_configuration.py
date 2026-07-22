"""Unit tests for argus.configuration.Configuration."""

import json
import tempfile
import unittest
from pathlib import Path

from argus.configuration import Configuration, ConfigurationError


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.tmp_path = Path(self._tmp_dir.name)

    def test_load_falls_back_to_defaults_when_file_missing(self):
        missing_path = self.tmp_path / "does_not_exist.json"

        configuration = Configuration.load(missing_path)

        self.assertEqual(configuration.get("app_name"), "ArgusOS")
        self.assertEqual(configuration.get("logging"), {"level": "INFO"})

    def test_load_merges_file_values_over_defaults(self):
        config_path = self.tmp_path / "config.json"
        config_path.write_text(json.dumps({"environment": "production"}))

        configuration = Configuration.load(config_path)

        self.assertEqual(configuration.get("environment"), "production")
        # Untouched defaults remain present.
        self.assertEqual(configuration.get("app_name"), "ArgusOS")

    def test_load_raises_on_invalid_json(self):
        config_path = self.tmp_path / "config.json"
        config_path.write_text("{not valid json")

        with self.assertRaises(ConfigurationError):
            Configuration.load(config_path)

    def test_load_raises_when_file_is_not_a_json_object(self):
        config_path = self.tmp_path / "config.json"
        config_path.write_text(json.dumps([1, 2, 3]))

        with self.assertRaises(ConfigurationError):
            Configuration.load(config_path)

    def test_get_returns_default_for_missing_key(self):
        configuration = Configuration({})

        self.assertEqual(configuration.get("missing", "fallback"), "fallback")

    def test_as_dict_returns_a_copy(self):
        configuration = Configuration({"a": 1})
        values = configuration.as_dict()
        values["a"] = 2

        self.assertEqual(configuration.get("a"), 1)


if __name__ == "__main__":
    unittest.main()
