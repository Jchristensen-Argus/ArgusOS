"""Unit tests for argus.events.event_bus.InMemoryEventBus."""

import logging
import unittest

from argus.events.event import Event
from argus.events.event_bus import InMemoryEventBus
from argus.events.event_types import EventType
from argus.events.exceptions import EventValidationError, SubscriptionError


def _bus() -> InMemoryEventBus:
    logger = logging.getLogger("argus.events.test")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return InMemoryEventBus(logger=logger)


class SubscribeUnsubscribeTests(unittest.TestCase):
    def test_subscribe_then_publish_invokes_handler(self):
        bus = _bus()
        received = []
        bus.subscribe(EventType.SYSTEM_STARTED, received.append)

        event = Event(type=EventType.SYSTEM_STARTED, source="test")
        bus.publish(event)

        self.assertEqual(received, [event])

    def test_unsubscribe_removes_handler(self):
        bus = _bus()
        received = []
        handler = received.append
        bus.subscribe(EventType.SYSTEM_STARTED, handler)
        bus.unsubscribe(EventType.SYSTEM_STARTED, handler)

        bus.publish(Event(type=EventType.SYSTEM_STARTED, source="test"))

        self.assertEqual(received, [])

    def test_unsubscribe_unknown_handler_raises(self):
        bus = _bus()

        with self.assertRaises(SubscriptionError):
            bus.unsubscribe(EventType.SYSTEM_STARTED, lambda event: None)

    def test_duplicate_subscription_raises(self):
        bus = _bus()
        handler = lambda event: None
        bus.subscribe(EventType.SYSTEM_STARTED, handler)

        with self.assertRaises(SubscriptionError):
            bus.subscribe(EventType.SYSTEM_STARTED, handler)

    def test_subscribe_rejects_non_callable_handler(self):
        bus = _bus()

        with self.assertRaises(SubscriptionError):
            bus.subscribe(EventType.SYSTEM_STARTED, "not callable")

    def test_subscribe_rejects_invalid_event_type(self):
        bus = _bus()

        with self.assertRaises(SubscriptionError):
            bus.subscribe("not-an-event-type", lambda event: None)

    def test_same_handler_can_subscribe_to_different_event_types(self):
        bus = _bus()
        received = []
        handler = received.append
        bus.subscribe(EventType.SYSTEM_STARTED, handler)
        bus.subscribe(EventType.SYSTEM_STOPPED, handler)

        bus.publish(Event(type=EventType.SYSTEM_STARTED, source="test"))
        bus.publish(Event(type=EventType.SYSTEM_STOPPED, source="test"))

        self.assertEqual(len(received), 2)


class PublishTests(unittest.TestCase):
    def test_multiple_subscribers_all_receive_the_event(self):
        bus = _bus()
        logger_calls = []
        memory_calls = []
        bus.subscribe(EventType.SYSTEM_STARTED, logger_calls.append)
        bus.subscribe(EventType.SYSTEM_STARTED, memory_calls.append)

        event = Event(type=EventType.SYSTEM_STARTED, source="Bootstrap")
        bus.publish(event)

        self.assertEqual(logger_calls, [event])
        self.assertEqual(memory_calls, [event])

    def test_handlers_execute_in_registration_order(self):
        bus = _bus()
        order = []
        bus.subscribe(EventType.SYSTEM_STARTED, lambda event: order.append("first"))
        bus.subscribe(EventType.SYSTEM_STARTED, lambda event: order.append("second"))
        bus.subscribe(EventType.SYSTEM_STARTED, lambda event: order.append("third"))

        bus.publish(Event(type=EventType.SYSTEM_STARTED, source="test"))

        self.assertEqual(order, ["first", "second", "third"])

    def test_publish_with_no_subscribers_does_not_raise(self):
        bus = _bus()

        bus.publish(Event(type=EventType.SYSTEM_STARTED, source="test"))

    def test_publish_none_raises_event_validation_error(self):
        bus = _bus()

        with self.assertRaises(EventValidationError):
            bus.publish(None)

    def test_publish_event_with_invalid_type_raises(self):
        bus = _bus()

        class FakeEvent:
            type = "not-an-event-type"
            source = "test"

        with self.assertRaises(EventValidationError):
            bus.publish(FakeEvent())

    def test_publish_event_with_missing_source_raises(self):
        bus = _bus()

        with self.assertRaises(EventValidationError):
            bus.publish(Event(type=EventType.SYSTEM_STARTED, source=""))

    def test_handler_cannot_mutate_the_published_event(self):
        bus = _bus()

        def handler(event):
            with self.assertRaises(Exception):
                event.source = "mutated"

        bus.subscribe(EventType.SYSTEM_STARTED, handler)
        bus.publish(Event(type=EventType.SYSTEM_STARTED, source="test"))


class DispatchTests(unittest.TestCase):
    def test_dispatch_only_calls_handlers_for_matching_type(self):
        bus = _bus()
        started_calls = []
        stopped_calls = []
        bus.subscribe(EventType.SYSTEM_STARTED, started_calls.append)
        bus.subscribe(EventType.SYSTEM_STOPPED, stopped_calls.append)

        bus.dispatch(Event(type=EventType.SYSTEM_STARTED, source="test"))

        self.assertEqual(len(started_calls), 1)
        self.assertEqual(len(stopped_calls), 0)


class LoggingTests(unittest.TestCase):
    def test_publish_emits_a_log_record(self):
        logger = logging.getLogger("argus.events.logging_test")
        logger.setLevel(logging.INFO)
        bus = InMemoryEventBus(logger=logger)
        bus.subscribe(EventType.SYSTEM_STARTED, lambda event: None)

        with self.assertLogs(logger, level="INFO") as captured:
            bus.publish(Event(type=EventType.SYSTEM_STARTED, source="Bootstrap"))

        self.assertEqual(len(captured.records), 1)
        message = captured.records[0].getMessage()
        self.assertIn("SYSTEM_STARTED", message)
        self.assertIn("Bootstrap", message)
        self.assertIn("NORMAL", message)
        self.assertIn("handlers=1", message)
        self.assertIn("duration_ms=", message)


if __name__ == "__main__":
    unittest.main()
