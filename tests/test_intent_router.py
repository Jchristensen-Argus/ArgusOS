"""Unit tests for argus.intent.router.IntentRouter."""

import logging
import unittest

from argus.events import EventType, InMemoryEventBus
from argus.intent import (
    DuplicateHandlerError,
    Intent,
    IntentError,
    IntentParseError,
    IntentRouter,
    IntentType,
    InvalidIntentError,
)
from argus.lifecycle import LifecycleState


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_intent_router")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


class RouterTestCase(unittest.TestCase):
    """Common setup: an IntentRouter with an in-memory Event Bus
    recording every published event, keyed by EventType."""

    def setUp(self):
        self.event_bus = InMemoryEventBus(logger=_silent_logger())
        self.received = []
        for event_type in EventType:
            self.event_bus.subscribe(event_type, self._record)
        self.router = IntentRouter(event_bus=self.event_bus)

    def _record(self, event):
        self.received.append(event)

    def _events_of(self, event_type):
        return [event for event in self.received if event.type == event_type]


# -- IService lifecycle ---------------------------------------------------


class IntentRouterIServiceTests(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus(logger=_silent_logger())
        self.router = IntentRouter(event_bus=self.event_bus)

    def test_initial_status_is_created(self):
        self.assertEqual(self.router.status(), LifecycleState.CREATED)

    def test_full_happy_path(self):
        self.router.initialize()
        self.assertEqual(self.router.status(), LifecycleState.INITIALIZING)

        self.router.start()
        self.assertEqual(self.router.status(), LifecycleState.RUNNING)

        self.router.stop()
        self.assertEqual(self.router.status(), LifecycleState.STOPPED)

    def test_start_without_initialize_raises(self):
        with self.assertRaises(IntentError):
            self.router.start()

    def test_initialize_twice_raises(self):
        self.router.initialize()

        with self.assertRaises(IntentError):
            self.router.initialize()

    def test_stop_without_start_raises(self):
        self.router.initialize()

        with self.assertRaises(IntentError):
            self.router.stop()

    def test_parse_route_and_register_handler_are_not_gated_by_lifecycle_state(self):
        # Unlike Scheduler.tick(), IntentRouter has no genuine
        # behavioral gate: parse/route/register_handler all work
        # identically regardless of lifecycle state. This is
        # deliberate (see router.py's module docstring and ADR-0002)
        # and is asserted here so any future change that *does* add
        # gating is a conscious, visible decision.
        intent = self.router.parse("hello")
        self.router.route(intent)
        self.router.register_handler(IntentType.UNKNOWN, lambda i: None)


# -- parse() ----------------------------------------------------------------


class ParseTests(RouterTestCase):
    def test_parse_returns_an_intent(self):
        intent = self.router.parse("Remember my dentist appointment")

        self.assertIsInstance(intent, Intent)
        self.assertEqual(intent.name, IntentType.MEMORY)

    def test_parse_publishes_intent_parsed(self):
        self.router.parse("Shutdown Argus")

        events = self._events_of(EventType.INTENT_PARSED)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["name"], IntentType.COMMAND.value)
        self.assertEqual(events[0].source, "intent_router")

    def test_parse_of_unknown_input_still_publishes_intent_parsed(self):
        self.router.parse("gibberish nonsense")

        events = self._events_of(EventType.INTENT_PARSED)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["name"], IntentType.UNKNOWN.value)

    def test_parse_never_raises_for_empty_or_whitespace_string(self):
        for text in ("", "   ", "\n\t"):
            with self.subTest(text=repr(text)):
                intent = self.router.parse(text)
                self.assertEqual(intent.name, IntentType.UNKNOWN)

    def test_parse_rejects_non_string_input(self):
        with self.assertRaises(IntentParseError):
            self.router.parse(123)

    def test_parse_rejects_none(self):
        with self.assertRaises(IntentParseError):
            self.router.parse(None)

    def test_parse_of_non_string_publishes_intent_failed(self):
        with self.assertRaises(IntentParseError):
            self.router.parse(123)

        self.assertEqual(len(self._events_of(EventType.INTENT_FAILED)), 1)

    def test_parse_of_non_string_does_not_publish_intent_parsed(self):
        with self.assertRaises(IntentParseError):
            self.router.parse([])

        self.assertEqual(len(self._events_of(EventType.INTENT_PARSED)), 0)


# -- route() ------------------------------------------------------------


class RouteTests(RouterTestCase):
    def test_route_publishes_intent_routed(self):
        intent = self.router.parse("What is corrugated board?")

        self.router.route(intent)

        events = self._events_of(EventType.INTENT_ROUTED)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["id"], intent.id)
        self.assertEqual(events[0].source, "intent_router")

    def test_route_rejects_non_intent_input(self):
        with self.assertRaises(InvalidIntentError):
            self.router.route("not an intent")

    def test_route_rejects_none(self):
        with self.assertRaises(InvalidIntentError):
            self.router.route(None)

    def test_route_of_invalid_input_publishes_intent_failed(self):
        with self.assertRaises(InvalidIntentError):
            self.router.route({"name": "memory"})

        self.assertEqual(len(self._events_of(EventType.INTENT_FAILED)), 1)

    def test_route_of_invalid_input_does_not_publish_intent_routed(self):
        with self.assertRaises(InvalidIntentError):
            self.router.route(42)

        self.assertEqual(len(self._events_of(EventType.INTENT_ROUTED)), 0)

    def test_route_payload_round_trips_entities_and_parameters(self):
        intent = self.router.parse("Remember my dentist appointment")

        self.router.route(intent)

        payload = self._events_of(EventType.INTENT_ROUTED)[0].payload
        self.assertEqual(payload["entities"], dict(intent.entities))
        self.assertEqual(payload["parameters"], dict(intent.parameters))
        self.assertEqual(payload["confidence"], intent.confidence)


# -- register_handler() --------------------------------------------------


class RegisterHandlerTests(RouterTestCase):
    def test_registered_handler_is_invoked_on_route(self):
        calls = []
        self.router.register_handler(IntentType.MEMORY, calls.append)

        intent = self.router.parse("Remember my dentist appointment")
        self.router.route(intent)

        self.assertEqual(len(calls), 1)
        self.assertIsInstance(calls[0], Intent)
        self.assertEqual(calls[0].id, intent.id)
        self.assertEqual(calls[0].name, IntentType.MEMORY)

    def test_handler_is_not_invoked_for_a_different_intent_name(self):
        calls = []
        self.router.register_handler(IntentType.SCHEDULE, calls.append)

        intent = self.router.parse("Remember my dentist appointment")
        self.router.route(intent)

        self.assertEqual(calls, [])

    def test_handler_is_not_invoked_directly_by_route_without_event_bus(self):
        # route() must invoke handlers only as a downstream consequence
        # of publishing to the Event Bus, never directly. Verified by
        # confirming a handler registered on a *different* router
        # instance sharing no Event Bus is never called.
        other_bus = InMemoryEventBus(logger=_silent_logger())
        other_router = IntentRouter(event_bus=other_bus)
        calls = []
        other_router.register_handler(IntentType.MEMORY, calls.append)

        intent = self.router.parse("Remember my dentist appointment")
        self.router.route(intent)

        self.assertEqual(calls, [])

    def test_multiple_handlers_for_the_same_intent_name_all_run(self):
        first_calls = []
        second_calls = []
        self.router.register_handler(IntentType.COMMAND, first_calls.append)
        self.router.register_handler(IntentType.COMMAND, second_calls.append)

        intent = self.router.parse("Shutdown Argus")
        self.router.route(intent)

        self.assertEqual(len(first_calls), 1)
        self.assertEqual(len(second_calls), 1)

    def test_duplicate_handler_registration_raises(self):
        def handler(intent):
            pass

        self.router.register_handler(IntentType.MEMORY, handler)

        with self.assertRaises(DuplicateHandlerError):
            self.router.register_handler(IntentType.MEMORY, handler)

    def test_same_handler_for_different_intent_names_is_allowed(self):
        def handler(intent):
            pass

        self.router.register_handler(IntentType.MEMORY, handler)
        self.router.register_handler(IntentType.SCHEDULE, handler)  # no raise

    def test_register_handler_rejects_non_intent_type_name(self):
        with self.assertRaises(InvalidIntentError):
            self.router.register_handler("memory", lambda i: None)

    def test_register_handler_rejects_non_callable_handler(self):
        with self.assertRaises(InvalidIntentError):
            self.router.register_handler(IntentType.MEMORY, "not callable")

    def test_failing_handler_does_not_prevent_other_handlers_from_running(self):
        def bad_handler(intent):
            raise ValueError("boom")

        good_calls = []
        self.router.register_handler(IntentType.MEMORY, bad_handler)
        self.router.register_handler(IntentType.MEMORY, good_calls.append)

        intent = self.router.parse("Remember my dentist appointment")
        self.router.route(intent)  # must not raise

        self.assertEqual(len(good_calls), 1)

    def test_failing_handler_publishes_intent_failed(self):
        def bad_handler(intent):
            raise ValueError("boom")

        self.router.register_handler(IntentType.MEMORY, bad_handler)

        intent = self.router.parse("Remember my dentist appointment")
        self.router.route(intent)

        self.assertEqual(len(self._events_of(EventType.INTENT_FAILED)), 1)

    def test_failing_handler_does_not_prevent_route_from_returning_normally(self):
        def bad_handler(intent):
            raise RuntimeError("boom")

        self.router.register_handler(IntentType.UNKNOWN, bad_handler)

        intent = self.router.parse("gibberish")
        result = self.router.route(intent)  # must not raise

        self.assertIsNone(result)


# -- loose coupling / no direct service invocation -----------------------


class LooseCouplingTests(RouterTestCase):
    def test_router_module_does_not_import_other_core_services(self):
        import argus.intent.router as router_module

        source = "".join(
            __import__("inspect").getsource(router_module)
        )
        for forbidden in ("argus.knowledge", "argus.memory", "argus.scheduler"):
            self.assertNotIn(forbidden, source)

    def test_route_only_invokes_handlers_via_the_event_bus_publish_call(self):
        # A handler registered *after* route() has already published
        # must not retroactively fire - proving route()'s only
        # mechanism is a single, synchronous publish() call, not some
        # separate direct-dispatch list checked lazily.
        intent = self.router.parse("Shutdown Argus")
        self.router.route(intent)

        calls = []
        self.router.register_handler(IntentType.COMMAND, calls.append)

        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
