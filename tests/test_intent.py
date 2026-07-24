"""Unit tests for argus.intent.intent (IntentType, Intent)."""

import unittest
from datetime import datetime, timezone
from types import MappingProxyType

from argus.intent import Intent, IntentType


class IntentTypeTests(unittest.TestCase):
    def test_expected_members_exist(self):
        self.assertEqual(
            {member.name for member in IntentType},
            {"QUESTION", "COMMAND", "MEMORY", "SCHEDULE", "UNKNOWN"},
        )

    def test_members_have_unique_string_values(self):
        values = [member.value for member in IntentType]

        self.assertEqual(len(values), len(set(values)))
        self.assertTrue(all(isinstance(v, str) for v in values))


class IntentConstructionTests(unittest.TestCase):
    def test_minimal_construction_defaults(self):
        intent = Intent(name=IntentType.QUESTION, confidence=1.0)

        self.assertEqual(intent.name, IntentType.QUESTION)
        self.assertEqual(intent.confidence, 1.0)
        self.assertEqual(intent.entities, {})
        self.assertEqual(intent.parameters, {})
        self.assertIsInstance(intent.id, str)
        self.assertTrue(intent.id)
        self.assertIsInstance(intent.timestamp, datetime)

    def test_id_defaults_are_unique_per_instance(self):
        first = Intent(name=IntentType.UNKNOWN, confidence=0.0)
        second = Intent(name=IntentType.UNKNOWN, confidence=0.0)

        self.assertNotEqual(first.id, second.id)

    def test_timestamp_defaults_to_utc_aware_now(self):
        intent = Intent(name=IntentType.UNKNOWN, confidence=0.0)

        self.assertIsNotNone(intent.timestamp.tzinfo)
        self.assertEqual(intent.timestamp.tzinfo, timezone.utc)

    def test_explicit_fields_are_honored(self):
        ts = datetime(2026, 1, 1, tzinfo=timezone.utc)

        intent = Intent(
            name=IntentType.COMMAND,
            confidence=0.6,
            id="fixed-id",
            entities={"verb": "shutdown"},
            parameters={"raw_text": "Shutdown Argus"},
            timestamp=ts,
        )

        self.assertEqual(intent.id, "fixed-id")
        self.assertEqual(intent.entities, {"verb": "shutdown"})
        self.assertEqual(intent.parameters, {"raw_text": "Shutdown Argus"})
        self.assertEqual(intent.timestamp, ts)


class IntentImmutabilityTests(unittest.TestCase):
    def test_intent_is_frozen(self):
        intent = Intent(name=IntentType.UNKNOWN, confidence=0.0)

        with self.assertRaises(Exception):
            intent.confidence = 1.0

    def test_entities_is_read_only_mapping(self):
        intent = Intent(name=IntentType.MEMORY, confidence=1.0, entities={"keyword": "remember"})

        self.assertIsInstance(intent.entities, MappingProxyType)
        with self.assertRaises(TypeError):
            intent.entities["keyword"] = "changed"

    def test_parameters_is_read_only_mapping(self):
        intent = Intent(name=IntentType.MEMORY, confidence=1.0, parameters={"raw_text": "x"})

        self.assertIsInstance(intent.parameters, MappingProxyType)
        with self.assertRaises(TypeError):
            intent.parameters["raw_text"] = "changed"

    def test_mutating_source_dict_after_construction_does_not_affect_intent(self):
        source = {"keyword": "remember"}
        intent = Intent(name=IntentType.MEMORY, confidence=1.0, entities=source)

        source["keyword"] = "mutated"

        self.assertEqual(intent.entities["keyword"], "remember")


if __name__ == "__main__":
    unittest.main()
