"""Unit tests for argus.memory_integration.integration.MemoryIntegration."""

import logging
import unittest
from typing import Sequence

from argus.events import EventType, InMemoryEventBus
from argus.knowledge_graph import KnowledgeGraph
from argus.knowledge_graph.exceptions import InvalidEntityError
from argus.lifecycle import LifecycleState
from argus.memory import MemoryRecord, MemoryService
from argus.memory.interfaces import IMemoryStorage
from argus.memory_integration import (
    InvalidMemoryIntegrationStateError,
    InvalidMemoryRecordError,
    MemoryIntegration,
    MemoryMappingError,
    MemoryNotSynchronizedError,
)


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_memory_integration")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


class _FlakyGraphWrapper:
    """Delegates every call to a real KnowledgeGraph except
    add_entity(), which raises for one specific, pre-chosen entity id
    - used only to exercise synchronize_all()'s "one failure does not
    abort the batch" behavior with a genuine failure, since a validly
    stored MemoryRecord can never legitimately fail translation on its
    own (MemoryService itself forbids empty keys)."""

    def __init__(self, graph: KnowledgeGraph, *, fail_entity_id: str):
        self._graph = graph
        self._fail_entity_id = fail_entity_id

    def add_entity(self, entity):
        if entity.id == self._fail_entity_id:
            raise InvalidEntityError(f"Simulated failure for {entity.id!r}.")
        return self._graph.add_entity(entity)

    def __getattr__(self, name):
        return getattr(self._graph, name)


class _InMemoryStorage(IMemoryStorage):
    """A minimal, fully in-memory IMemoryStorage stand-in - no disk
    I/O of any kind - used so tests never touch memory_store.json."""

    def __init__(self):
        self._records = []

    def load(self) -> Sequence[MemoryRecord]:
        return tuple(self._records)

    def save(self, records: Sequence[MemoryRecord]) -> None:
        self._records = list(records)


class MemoryIntegrationTestCase(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus(logger=_silent_logger())
        self.received = []
        for event_type in (
            EventType.MEMORY_SYNCHRONIZED,
            EventType.MEMORY_DESYNCHRONIZED,
            EventType.MEMORY_MAPPING_FAILED,
        ):
            self.event_bus.subscribe(event_type, self.received.append)
        self.memory_service = MemoryService(storage=_InMemoryStorage(), event_bus=self.event_bus)
        self.graph = KnowledgeGraph(event_bus=self.event_bus)
        self.integration = MemoryIntegration(
            memory_service=self.memory_service,
            knowledge_graph=self.graph,
            event_bus=self.event_bus,
        )

    def _running(self):
        self.integration.initialize()
        self.integration.start()
        return self.integration

    def _put(self, key, value):
        self.memory_service.put(MemoryRecord(key=key, value=value))


class ConstructionTests(MemoryIntegrationTestCase):
    def test_starts_in_created_state(self):
        self.assertEqual(self.integration.status(), LifecycleState.CREATED)

    def test_starts_with_empty_synchronization_status(self):
        status = self.integration.synchronization_status()

        self.assertEqual(status["synchronized_count"], 0)
        self.assertEqual(status["failed_count"], 0)


class LifecycleGateTests(MemoryIntegrationTestCase):
    def test_synchronize_memory_before_running_raises(self):
        self._put("alice", {"name": "Alice"})

        with self.assertRaises(InvalidMemoryIntegrationStateError):
            self.integration.synchronize_memory("alice")

    def test_remove_memory_before_running_raises(self):
        with self.assertRaises(InvalidMemoryIntegrationStateError):
            self.integration.remove_memory("alice")

    def test_synchronize_all_before_running_raises(self):
        with self.assertRaises(InvalidMemoryIntegrationStateError):
            self.integration.synchronize_all()

    def test_synchronization_status_is_ungated(self):
        # No initialize()/start() call at all - still works.
        self.integration.synchronization_status()

    def test_reset_is_ungated(self):
        self.integration.reset()

    def test_initialize_then_start_transitions_to_running(self):
        self._running()

        self.assertEqual(self.integration.status(), LifecycleState.RUNNING)

    def test_stop_transitions_to_stopped(self):
        self._running()
        self.integration.stop()

        self.assertEqual(self.integration.status(), LifecycleState.STOPPED)

    def test_start_before_initialize_raises(self):
        with self.assertRaises(Exception):
            self.integration.start()

    def test_stop_before_start_raises(self):
        self.integration.initialize()

        with self.assertRaises(Exception):
            self.integration.stop()

    def test_operations_gated_again_after_stop(self):
        self._running()
        self.integration.stop()

        with self.assertRaises(InvalidMemoryIntegrationStateError):
            self.integration.synchronize_memory("alice")

    def test_initialize_twice_raises(self):
        self.integration.initialize()

        with self.assertRaises(Exception):
            self.integration.initialize()


class SynchronizationTests(MemoryIntegrationTestCase):
    def test_synchronize_unknown_key_raises(self):
        self._running()

        with self.assertRaises(InvalidMemoryRecordError):
            self.integration.synchronize_memory("unknown")

    def test_synchronize_empty_key_raises(self):
        self._running()

        with self.assertRaises(InvalidMemoryRecordError):
            self.integration.synchronize_memory("")

    def test_synchronize_creates_entity(self):
        self._running()
        self._put("alice", {"name": "Alice"})

        entity_id = self.integration.synchronize_memory("alice")

        self.assertEqual(entity_id, "memory:alice")
        entity = self.graph.get_entity("memory:alice")
        self.assertEqual(entity.name, "alice")
        self.assertEqual(entity.attributes["value"], {"name": "Alice"})

    def test_synchronize_publishes_memory_synchronized(self):
        self._running()
        self._put("alice", {"name": "Alice"})

        self.integration.synchronize_memory("alice")

        types = [event.type for event in self.received]
        self.assertIn(EventType.MEMORY_SYNCHRONIZED, types)

    def test_synchronize_updates_synchronization_status(self):
        self._running()
        self._put("alice", {"name": "Alice"})

        self.integration.synchronize_memory("alice")

        status = self.integration.synchronization_status()
        self.assertEqual(status["synchronized_count"], 1)
        self.assertIn("alice", status["synchronized_keys"])

    def test_duplicate_synchronization_does_not_create_a_second_entity(self):
        self._running()
        self._put("alice", {"name": "Alice"})

        self.integration.synchronize_memory("alice")
        self.integration.synchronize_memory("alice")

        self.assertEqual(len(self.graph.list_entities()), 1)

    def test_synchronize_again_updates_the_entity_in_place(self):
        self._running()
        self._put("alice", {"name": "Alice"})
        self.integration.synchronize_memory("alice")

        self.memory_service.update("alice", {"name": "Alice Updated"})
        self.integration.synchronize_memory("alice")

        entity = self.graph.get_entity("memory:alice")
        self.assertEqual(entity.attributes["value"], {"name": "Alice Updated"})
        self.assertEqual(len(self.graph.list_entities()), 1)

    def test_synchronize_translates_related_keys_into_relationships(self):
        self._running()
        self._put("alice", {"name": "Alice"})
        self._put("bob", {"name": "Bob", "related_keys": ["alice"]})

        self.integration.synchronize_memory("alice")
        self.integration.synchronize_memory("bob")

        relationships = self.graph.list_relationships()
        self.assertEqual(len(relationships), 1)
        self.assertEqual(relationships[0].source_entity_id, "memory:bob")
        self.assertEqual(relationships[0].target_entity_id, "memory:alice")

    def test_relationship_to_unsynchronized_key_fails_without_aborting_entity_sync(self):
        self._running()
        self._put("bob", {"name": "Bob", "related_keys": ["ghost"]})

        entity_id = self.integration.synchronize_memory("bob")

        self.assertEqual(entity_id, "memory:bob")
        self.assertEqual(self.graph.list_relationships(), ())

    def test_relationship_failure_publishes_memory_mapping_failed(self):
        self._running()
        self._put("bob", {"name": "Bob", "related_keys": ["ghost"]})

        self.integration.synchronize_memory("bob")

        types = [event.type for event in self.received]
        self.assertIn(EventType.MEMORY_MAPPING_FAILED, types)
        self.assertIn(EventType.MEMORY_SYNCHRONIZED, types)

    def test_resynchronizing_rebuilds_relationships_from_current_value(self):
        self._running()
        self._put("alice", {"name": "Alice"})
        self._put("carol", {"name": "Carol"})
        self._put("bob", {"name": "Bob", "related_keys": ["alice"]})
        self.integration.synchronize_memory("alice")
        self.integration.synchronize_memory("carol")
        self.integration.synchronize_memory("bob")
        self.assertEqual(len(self.graph.list_relationships()), 1)

        self.memory_service.update("bob", {"name": "Bob", "related_keys": ["carol"]})
        self.integration.synchronize_memory("bob")

        relationships = self.graph.list_relationships()
        self.assertEqual(len(relationships), 1)
        self.assertEqual(relationships[0].target_entity_id, "memory:carol")


class RemovalTests(MemoryIntegrationTestCase):
    def test_remove_unsynchronized_key_raises(self):
        self._running()

        with self.assertRaises(MemoryNotSynchronizedError):
            self.integration.remove_memory("alice")

    def test_remove_removes_entity(self):
        self._running()
        self._put("alice", {"name": "Alice"})
        self.integration.synchronize_memory("alice")

        self.integration.remove_memory("alice")

        self.assertEqual(self.graph.list_entities(), ())

    def test_remove_publishes_memory_desynchronized(self):
        self._running()
        self._put("alice", {"name": "Alice"})
        self.integration.synchronize_memory("alice")

        self.integration.remove_memory("alice")

        types = [event.type for event in self.received]
        self.assertIn(EventType.MEMORY_DESYNCHRONIZED, types)

    def test_remove_clears_synchronization_bookkeeping(self):
        self._running()
        self._put("alice", {"name": "Alice"})
        self.integration.synchronize_memory("alice")

        self.integration.remove_memory("alice")

        status = self.integration.synchronization_status()
        self.assertEqual(status["synchronized_count"], 0)

    def test_removing_an_entity_cascades_relationships(self):
        self._running()
        self._put("alice", {"name": "Alice"})
        self._put("bob", {"name": "Bob", "related_keys": ["alice"]})
        self.integration.synchronize_memory("alice")
        self.integration.synchronize_memory("bob")
        self.assertEqual(len(self.graph.list_relationships()), 1)

        self.integration.remove_memory("alice")

        self.assertEqual(self.graph.list_relationships(), ())

    def test_removing_does_not_affect_unrelated_synchronized_entities(self):
        self._running()
        self._put("alice", {"name": "Alice"})
        self._put("carol", {"name": "Carol"})
        self.integration.synchronize_memory("alice")
        self.integration.synchronize_memory("carol")

        self.integration.remove_memory("alice")

        self.assertEqual(len(self.graph.list_entities()), 1)
        self.assertEqual(self.graph.list_entities()[0].name, "carol")

    def test_remove_tolerates_entity_already_gone_from_graph(self):
        # A key MemoryIntegration's own bookkeeping still considers
        # synchronized, but whose Entity was already removed directly
        # from the Knowledge Graph by something else - remove_memory()
        # must still clear its own bookkeeping and publish
        # MEMORY_DESYNCHRONIZED, not raise.
        self._running()
        self._put("alice", {"name": "Alice"})
        self.integration.synchronize_memory("alice")
        self.graph.remove_entity("memory:alice")

        self.integration.remove_memory("alice")

        status = self.integration.synchronization_status()
        self.assertEqual(status["synchronized_count"], 0)
        types = [event.type for event in self.received]
        self.assertIn(EventType.MEMORY_DESYNCHRONIZED, types)


class SynchronizeAllTests(MemoryIntegrationTestCase):
    def test_synchronizes_every_record(self):
        self._running()
        self._put("alice", {"name": "Alice"})
        self._put("bob", {"name": "Bob"})

        synchronized = self.integration.synchronize_all()

        self.assertEqual(set(synchronized), {"alice", "bob"})
        self.assertEqual(len(self.graph.list_entities()), 2)

    def test_empty_memory_service_synchronizes_nothing(self):
        self._running()

        self.assertEqual(self.integration.synchronize_all(), ())

    def test_one_failure_does_not_abort_the_batch(self):
        flaky_graph = _FlakyGraphWrapper(self.graph, fail_entity_id="memory:bob")
        integration = MemoryIntegration(
            memory_service=self.memory_service, knowledge_graph=flaky_graph, event_bus=self.event_bus
        )
        integration.initialize()
        integration.start()
        self._put("alice", {"name": "Alice"})
        self._put("bob", {"name": "Bob"})

        synchronized = integration.synchronize_all()

        self.assertEqual(synchronized, ("alice",))
        status = integration.synchronization_status()
        self.assertIn("bob", status["failed_keys"])

    def test_batch_failure_publishes_memory_mapping_failed(self):
        flaky_graph = _FlakyGraphWrapper(self.graph, fail_entity_id="memory:bob")
        integration = MemoryIntegration(
            memory_service=self.memory_service, knowledge_graph=flaky_graph, event_bus=self.event_bus
        )
        integration.initialize()
        integration.start()
        self._put("bob", {"name": "Bob"})

        integration.synchronize_all()

        types = [event.type for event in self.received]
        self.assertIn(EventType.MEMORY_MAPPING_FAILED, types)

    def test_entity_level_failure_raises_memory_mapping_error(self):
        flaky_graph = _FlakyGraphWrapper(self.graph, fail_entity_id="memory:bob")
        integration = MemoryIntegration(
            memory_service=self.memory_service, knowledge_graph=flaky_graph, event_bus=self.event_bus
        )
        integration.initialize()
        integration.start()
        self._put("bob", {"name": "Bob"})

        with self.assertRaises(MemoryMappingError):
            integration.synchronize_memory("bob")


class SynchronizationStatusAndResetTests(MemoryIntegrationTestCase):
    def test_status_reports_failed_keys(self):
        self._running()
        self._put("bob", {"name": "Bob", "related_keys": ["ghost"]})

        self.integration.synchronize_memory("bob")

        status = self.integration.synchronization_status()
        # Entity sync succeeded; only the relationship failed, which
        # does not populate self._failed (that only tracks Entity-level
        # failures) - confirm entity-level bookkeeping is clean.
        self.assertEqual(status["synchronized_count"], 1)
        self.assertEqual(status["failed_count"], 0)

    def test_reset_clears_bookkeeping_only(self):
        self._running()
        self._put("alice", {"name": "Alice"})
        self.integration.synchronize_memory("alice")

        self.integration.reset()

        status = self.integration.synchronization_status()
        self.assertEqual(status["synchronized_count"], 0)
        # Graph and memory service are untouched by reset().
        self.assertEqual(len(self.graph.list_entities()), 1)
        self.assertTrue(self.memory_service.exists("alice"))

    def test_reset_does_not_gate_on_lifecycle_state(self):
        # Never initialized/started - reset() still works.
        self.integration.reset()


class GraphConsistencyTests(MemoryIntegrationTestCase):
    def test_graph_never_contains_duplicate_entity_ids(self):
        self._running()
        self._put("alice", {"name": "Alice"})

        for _ in range(3):
            self.integration.synchronize_memory("alice")

        ids = [entity.id for entity in self.graph.list_entities()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_mapper_is_never_called_directly_by_tests_but_produces_matching_ids(self):
        self._running()
        self._put("alice", {"name": "Alice"})

        entity_id = self.integration.synchronize_memory("alice")

        self.assertEqual(entity_id, self.graph.get_entity(entity_id).id)


if __name__ == "__main__":
    unittest.main()
