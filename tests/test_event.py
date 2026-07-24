"""Unit tests for argus.events.event.Event."""

import unittest
import uuid
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from argus.events.event import Event
from argus.events.event_types import EventPriority, EventType


class EventTests(unittest.TestCase):
    def test_id_is_generated_automatically(self):
        event = Event(type=EventType.SYSTEM_STARTED, source="test")

        self.assertIsInstance(event.id, uuid.UUID)

    def test_id_is_unique_per_event(self):
        first = Event(type=EventType.SYSTEM_STARTED, source="test")
        second = Event(type=EventType.SYSTEM_STARTED, source="test")

        self.assertNotEqual(first.id, second.id)

    def test_timestamp_is_generated_automatically_in_utc(self):
        before = datetime.now(timezone.utc)
        event = Event(type=EventType.SYSTEM_STARTED, source="test")
        after = datetime.now(timezone.utc)

        self.assertIsInstance(event.timestamp, datetime)
        self.assertEqual(event.timestamp.tzinfo, timezone.utc)
        self.assertTrue(before <= event.timestamp <= after)

    def test_payload_defaults_to_empty_mapping(self):
        event = Event(type=EventType.SYSTEM_STARTED, source="test")

        self.assertEqual(dict(event.payload), {})

    def test_metadata_defaults_to_empty_mapping(self):
        event = Event(type=EventType.SYSTEM_STARTED, source="test")

        self.assertEqual(dict(event.metadata), {})

    def test_priority_defaults_to_normal(self):
        event = Event(type=EventType.SYSTEM_STARTED, source="test")

        self.assertEqual(event.priority, EventPriority.NORMAL)

    def test_event_is_frozen(self):
        event = Event(type=EventType.SYSTEM_STARTED, source="test")

        with self.assertRaises(FrozenInstanceError):
            event.source = "changed"

    def test_payload_mapping_cannot_be_mutated(self):
        event = Event(
            type=EventType.SYSTEM_STARTED, source="test", payload={"key": "value"}
        )

        with self.assertRaises(TypeError):
            event.payload["key"] = "changed"

    def test_metadata_mapping_cannot_be_mutated(self):
        event = Event(
            type=EventType.SYSTEM_STARTED, source="test", metadata={"key": "value"}
        )

        with self.assertRaises(TypeError):
            event.metadata["key"] = "changed"

    def test_payload_and_metadata_values_are_preserved(self):
        event = Event(
            type=EventType.SYSTEM_STARTED,
            source="test",
            payload={"a": 1},
            metadata={"b": 2},
        )

        self.assertEqual(event.payload["a"], 1)
        self.assertEqual(event.metadata["b"], 2)


if __name__ == "__main__":
    unittest.main()
