"""Unit tests for argus.capability.registry.CapabilityRegistry."""

import logging
import unittest

from argus.capability import (
    Capability,
    CapabilityNotFoundError,
    CapabilityRegistry,
    DuplicateCapabilityError,
    ICapabilityRegistry,
    InvalidCapabilityError,
)
from argus.events import EventType, InMemoryEventBus
from argus.intent import IntentType


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_capability_registry")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


def _capability(**overrides):
    defaults = dict(
        name="Answer",
        description="Answers questions.",
        intent_types=[IntentType.QUESTION],
        action_kind="workflow",
        workflow_id="answer_workflow",
    )
    defaults.update(overrides)
    return Capability(**defaults)


class RegistryTestCase(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus(logger=_silent_logger())
        self.registry = CapabilityRegistry(event_bus=self.event_bus)
        self.received = []
        for event_type in EventType:
            self.event_bus.subscribe(event_type, self.received.append)


# -- interface / not-an-IService ------------------------------------------


class CapabilityRegistryIdentityTests(unittest.TestCase):
    def test_is_an_icapabilityregistry(self):
        registry = CapabilityRegistry(event_bus=InMemoryEventBus(logger=_silent_logger()))
        self.assertIsInstance(registry, ICapabilityRegistry)

    def test_is_not_an_iservice(self):
        # Deliberate: CapabilityRegistry does not adopt IService - see
        # argus/capability/interfaces.py's Architectural Note.
        from argus.lifecycle import IService

        registry = CapabilityRegistry(event_bus=InMemoryEventBus(logger=_silent_logger()))
        self.assertNotIsInstance(registry, IService)

    def test_all_registry_methods_available_immediately(self):
        # No lifecycle to initialize/start - every method works the
        # instant the registry is constructed.
        registry = CapabilityRegistry(event_bus=InMemoryEventBus(logger=_silent_logger()))
        registry.register(_capability())  # must not raise
        self.assertTrue(registry.contains(registry.list_capabilities()[0].id))


# -- register() -------------------------------------------------------------


class RegisterTests(RegistryTestCase):
    def test_register_makes_capability_discoverable(self):
        capability = _capability()

        self.registry.register(capability)

        self.assertTrue(self.registry.contains(capability.id))
        self.assertIs(self.registry.get(capability.id), capability)

    def test_register_rejects_non_capability(self):
        with self.assertRaises(InvalidCapabilityError):
            self.registry.register(object())

    def test_register_rejects_empty_id(self):
        with self.assertRaises(InvalidCapabilityError):
            self.registry.register(_capability(id=""))

    def test_register_rejects_empty_name(self):
        with self.assertRaises(InvalidCapabilityError):
            self.registry.register(_capability(name=""))

    def test_register_rejects_empty_intent_types(self):
        with self.assertRaises(InvalidCapabilityError):
            self.registry.register(_capability(intent_types=[]))

    def test_register_rejects_non_intent_type_entries(self):
        with self.assertRaises(InvalidCapabilityError):
            self.registry.register(_capability(intent_types=["question"]))

    def test_register_rejects_empty_action_kind(self):
        with self.assertRaises(InvalidCapabilityError):
            self.registry.register(_capability(action_kind=""))

    def test_register_rejects_workflow_kind_without_workflow_id(self):
        with self.assertRaises(InvalidCapabilityError):
            self.registry.register(_capability(action_kind="workflow", workflow_id=None))

    def test_register_allows_non_workflow_kind_without_workflow_id(self):
        self.registry.register(
            _capability(action_kind="plugin", workflow_id=None)
        )  # must not raise

    def test_duplicate_id_raises(self):
        capability = _capability(id="dup-id")
        self.registry.register(capability)

        with self.assertRaises(DuplicateCapabilityError):
            self.registry.register(_capability(id="dup-id"))

    def test_duplicate_name_raises(self):
        # Package 033: "Duplicate names are rejected." A different id
        # does not exempt a colliding name.
        self.registry.register(_capability(id="first", name="Answer"))

        with self.assertRaises(DuplicateCapabilityError):
            self.registry.register(_capability(id="second", name="Answer"))

    def test_duplicate_name_does_not_register_the_second_capability(self):
        self.registry.register(_capability(id="first", name="Answer"))

        with self.assertRaises(DuplicateCapabilityError):
            self.registry.register(_capability(id="second", name="Answer"))

        self.assertFalse(self.registry.contains("second"))
        self.assertEqual(len(self.registry.list_capabilities()), 1)

    def test_distinct_names_do_not_collide(self):
        self.registry.register(_capability(id="first", name="Answer"))
        self.registry.register(_capability(id="second", name="Different"))  # must not raise

        self.assertEqual(len(self.registry.list_capabilities()), 2)

    def test_register_after_unregister_succeeds(self):
        capability = _capability(id="reused-id")
        self.registry.register(capability)
        self.registry.unregister(capability.id)

        self.registry.register(_capability(id="reused-id"))  # must not raise

    def test_register_after_unregister_frees_the_name_too(self):
        # Package 033: unregistering a capability frees both its own
        # id and its own name for reuse.
        capability = _capability(id="original-id", name="Answer")
        self.registry.register(capability)
        self.registry.unregister(capability.id)

        self.registry.register(
            _capability(id="new-id", name="Answer")
        )  # must not raise
        self.assertTrue(self.registry.contains("new-id"))

    def test_register_publishes_capability_registered(self):
        capability = _capability()

        self.registry.register(capability)

        events = [e for e in self.received if e.type == EventType.CAPABILITY_REGISTERED]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["capability_id"], capability.id)
        self.assertEqual(events[0].payload["name"], capability.name)

    def test_failed_register_does_not_publish(self):
        with self.assertRaises(InvalidCapabilityError):
            self.registry.register(_capability(name=""))

        self.assertEqual(self.received, [])


# -- unregister() -------------------------------------------------------------


class UnregisterTests(RegistryTestCase):
    def test_unregister_removes_capability(self):
        capability = _capability()
        self.registry.register(capability)

        self.registry.unregister(capability.id)

        self.assertFalse(self.registry.contains(capability.id))

    def test_unregister_rejects_non_string(self):
        with self.assertRaises(InvalidCapabilityError):
            self.registry.unregister(123)

    def test_unregister_unknown_id_raises(self):
        with self.assertRaises(CapabilityNotFoundError):
            self.registry.unregister("missing")

    def test_unregister_publishes_capability_unregistered(self):
        capability = _capability()
        self.registry.register(capability)
        self.received.clear()

        self.registry.unregister(capability.id)

        events = [e for e in self.received if e.type == EventType.CAPABILITY_UNREGISTERED]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["capability_id"], capability.id)

    def test_failed_unregister_does_not_publish(self):
        with self.assertRaises(CapabilityNotFoundError):
            self.registry.unregister("missing")

        self.assertEqual(self.received, [])


# -- get() -------------------------------------------------------------


class GetTests(RegistryTestCase):
    def test_get_returns_registered_capability(self):
        capability = _capability()
        self.registry.register(capability)

        self.assertIs(self.registry.get(capability.id), capability)

    def test_get_rejects_non_string(self):
        with self.assertRaises(InvalidCapabilityError):
            self.registry.get(123)

    def test_get_unknown_id_raises(self):
        with self.assertRaises(CapabilityNotFoundError):
            self.registry.get("missing")


# -- get_by_name() (Package 033) ------------------------------------------


class GetByNameTests(RegistryTestCase):
    def test_get_by_name_returns_registered_capability(self):
        capability = _capability(name="Answer")
        self.registry.register(capability)

        self.assertIs(self.registry.get_by_name("Answer"), capability)

    def test_get_by_name_rejects_non_string(self):
        with self.assertRaises(InvalidCapabilityError):
            self.registry.get_by_name(123)

    def test_get_by_name_unknown_name_raises(self):
        with self.assertRaises(CapabilityNotFoundError):
            self.registry.get_by_name("missing")

    def test_get_by_name_after_unregister_raises(self):
        capability = _capability(name="Answer")
        self.registry.register(capability)
        self.registry.unregister(capability.id)

        with self.assertRaises(CapabilityNotFoundError):
            self.registry.get_by_name("Answer")

    def test_get_by_name_does_not_publish_events(self):
        self.registry.register(_capability(name="Answer"))
        self.received.clear()

        self.registry.get_by_name("Answer")

        self.assertEqual(self.received, [])


# -- find_by_intent_type() -------------------------------------------------------------


class FindByIntentTypeTests(RegistryTestCase):
    def test_returns_matching_capabilities(self):
        capability = _capability(intent_types=[IntentType.QUESTION])
        self.registry.register(capability)

        matches = self.registry.find_by_intent_type(IntentType.QUESTION)

        self.assertEqual(matches, (capability,))

    def test_returns_empty_for_no_matches(self):
        self.assertEqual(self.registry.find_by_intent_type(IntentType.QUESTION), ())

    def test_matches_capability_supporting_multiple_intent_types(self):
        capability = _capability(intent_types=[IntentType.QUESTION, IntentType.UNKNOWN])
        self.registry.register(capability)

        self.assertIn(capability, self.registry.find_by_intent_type(IntentType.UNKNOWN))

    def test_returns_disabled_capabilities_too(self):
        # find_by_intent_type() is a pure filter - it applies no
        # enabled/disabled policy. See ICapabilityRegistry's docstring.
        capability = _capability(enabled=False)
        self.registry.register(capability)

        self.assertIn(capability, self.registry.find_by_intent_type(IntentType.QUESTION))

    def test_returns_multiple_matches_in_registration_order(self):
        first = _capability(id="first")
        second = _capability(id="second", name="Second")
        self.registry.register(first)
        self.registry.register(second)

        self.assertEqual(
            self.registry.find_by_intent_type(IntentType.QUESTION), (first, second)
        )

    def test_rejects_non_intent_type(self):
        with self.assertRaises(InvalidCapabilityError):
            self.registry.find_by_intent_type("question")

    def test_does_not_publish_events(self):
        self.registry.register(_capability())
        self.received.clear()

        self.registry.find_by_intent_type(IntentType.QUESTION)

        self.assertEqual(self.received, [])


# -- list_capabilities() -------------------------------------------------------------


class ListCapabilitiesTests(RegistryTestCase):
    def test_empty_by_default(self):
        self.assertEqual(self.registry.list_capabilities(), ())

    def test_returns_every_registered_capability(self):
        a = _capability(id="a")
        b = _capability(id="b", name="B", intent_types=[IntentType.COMMAND])
        self.registry.register(a)
        self.registry.register(b)

        self.assertEqual(self.registry.list_capabilities(), (a, b))

    def test_excludes_unregistered_capabilities(self):
        a = _capability(id="a")
        self.registry.register(a)
        self.registry.unregister("a")

        self.assertEqual(self.registry.list_capabilities(), ())


# -- contains() -------------------------------------------------------------


class ContainsTests(RegistryTestCase):
    def test_true_for_registered(self):
        capability = _capability()
        self.registry.register(capability)

        self.assertTrue(self.registry.contains(capability.id))

    def test_false_for_unregistered(self):
        self.assertFalse(self.registry.contains("missing"))

    def test_false_for_non_string_never_raises(self):
        self.assertFalse(self.registry.contains(123))
        self.assertFalse(self.registry.contains(None))


if __name__ == "__main__":
    unittest.main()
