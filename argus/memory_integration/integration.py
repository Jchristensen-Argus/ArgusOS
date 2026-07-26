"""
MemoryIntegration: in-memory bridge between the Memory Service and the
Knowledge Graph for ArgusOS.

Purpose:
    Implement IMemoryIntegration: coordinate IMemoryService and
    IKnowledgeGraph so that memory records can become semantic
    knowledge through controlled synchronization, per
    factory/packages/019_MEMORY_INTEGRATION.md. "This package owns
    the bridge - not memory, not knowledge." MemoryIntegration never
    stores memory values itself (IMemoryService remains the sole
    source of truth for memory) and never stores graph structure
    itself (IKnowledgeGraph remains the sole source of truth for
    Entities/Relationships) - see "It Owns No Data Itself," below,
    for exactly what internal state it does keep and why that does
    not contradict this.

It Owns No Data Itself:
    MemoryIntegration keeps two small internal dicts -
    `self._synchronized` (key -> the Entity id most recently
    synchronized for that key) and `self._failed` (key -> the most
    recent synchronization failure's message) - purely as
    bookkeeping to support synchronization_status() and idempotent
    re-synchronization. Neither dict is a competing copy of memory
    values or graph structure: `self._synchronized`'s values are
    always exactly `f"memory:{key}"` (MemoryMapper's own deterministic
    scheme - see mapper.py), recoverable at any time without this
    bookkeeping at all, and `reset()` clears both dicts without
    touching the Memory Service or the Knowledge Graph in any way
    (see reset()'s own docstring). This is the same category of
    "lightweight bookkeeping, not a competing source of truth"
    already established by AgentRuntime's own Execution tracking
    (Package 016) and ConnectorManager's own Connector-metadata
    tracking (Package 017) - neither of those packages "owns" a Plan
    or an external system either, despite holding internal state
    about them.

Synchronization Semantics - Reconcile, Not Merge:
    Every synchronize_memory(key) call is fully idempotent and
    self-healing: if `key` has never been synchronized, its Entity is
    added fresh; if it has, the existing Entity (and, via
    IKnowledgeGraph's own cascading removal - Package 018 - every
    Relationship referencing it) is removed and rebuilt from the
    MemoryRecord's *current* state. This single mechanism satisfies
    both "prevent duplicate graph entities" (the same key always
    resolves to the same deterministic Entity id, so no duplicate can
    ever be created) and "synchronize updates" (each call reflects the
    record's current value) without a separate code path for either.
    See this module's own Known Limitation about resynchronization's
    effect on *other* entities' inbound Relationships, documented in
    factory/packages/019_MEMORY_INTEGRATION.md.

Responsibilities:
    - MemoryIntegration: the sole implementation of
      IMemoryIntegration.

Non-Responsibilities:
    - MemoryIntegration never modifies Planner or Runtime behavior,
      performs graph reasoning or inference, executes Plans, or
      communicates externally - see this package's Objective and
      Constraints.
    - MemoryIntegration never constructs an Entity or Relationship
      itself - every translation is delegated to the injected
      MemoryMapper (argus/memory_integration/mapper.py).

Dependencies:
    argus.events (Event, EventType, IEventBus), argus.knowledge_graph
    (IKnowledgeGraph and its exceptions), argus.lifecycle.lifecycle
    (LifecycleState), argus.memory (IMemoryService and its
    exceptions), argus.memory_integration.exceptions,
    argus.memory_integration.interfaces (IMemoryIntegration),
    argus.memory_integration.mapper (MemoryMapper).
"""

from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Sequence

from argus.events.event import Event
from argus.events.event_types import EventType
from argus.events.interfaces import IEventBus
from argus.knowledge_graph.exceptions import EntityNotFoundError, KnowledgeGraphError
from argus.knowledge_graph.interfaces import IKnowledgeGraph
from argus.lifecycle.lifecycle import LifecycleState
from argus.memory.exceptions import MemoryNotFoundError
from argus.memory.interfaces import IMemoryService
from argus.memory_integration.exceptions import (
    InvalidMemoryIntegrationStateError,
    InvalidMemoryRecordError,
    MemoryIntegrationError,
    MemoryMappingError,
    MemoryNotSynchronizedError,
)
from argus.memory_integration.interfaces import IMemoryIntegration
from argus.memory_integration.mapper import MemoryMapper


class MemoryIntegration(IMemoryIntegration):
    """
    In-memory implementation of IMemoryIntegration.

    Purpose:
        Coordinate an injected IMemoryService and IKnowledgeGraph,
        via an injected MemoryMapper, to translate memory records into
        graph knowledge on demand. See the module docstring for the
        full design rationale.

    Dependencies:
        An IMemoryService, an IKnowledgeGraph, an IEventBus, and
        (optionally) a MemoryMapper, all injected by the caller
        (bootstrap.py). If no MemoryMapper is given, a fresh one is
        constructed automatically.
    """

    def __init__(
        self,
        memory_service: IMemoryService,
        knowledge_graph: IKnowledgeGraph,
        event_bus: IEventBus,
        *,
        mapper: Optional[MemoryMapper] = None,
    ) -> None:
        self._memory_service = memory_service
        self._knowledge_graph = knowledge_graph
        self._event_bus = event_bus
        self._mapper = mapper if mapper is not None else MemoryMapper()
        self._synchronized: Dict[str, str] = {}
        self._failed: Dict[str, str] = {}
        self._state: LifecycleState = LifecycleState.CREATED

    # -- IService -----------------------------------------------------

    def initialize(self) -> None:
        if self._state != LifecycleState.CREATED:
            raise MemoryIntegrationError(
                f"Cannot initialize: MemoryIntegration is {self._state.name}, expected CREATED."
            )
        self._state = LifecycleState.INITIALIZING

    def start(self) -> None:
        if self._state != LifecycleState.INITIALIZING:
            raise MemoryIntegrationError(
                f"Cannot start: MemoryIntegration is {self._state.name}, expected INITIALIZING."
            )
        self._state = LifecycleState.RUNNING

    def stop(self) -> None:
        if self._state != LifecycleState.RUNNING:
            raise MemoryIntegrationError(
                f"Cannot stop: MemoryIntegration is {self._state.name}, expected RUNNING."
            )
        self._state = LifecycleState.STOPPING
        self._state = LifecycleState.STOPPED

    def status(self) -> LifecycleState:
        return self._state

    # -- IMemoryIntegration: gated (real cross-system coordination) -----

    def synchronize_memory(self, key: str) -> str:
        self._require_running("synchronize_memory")
        record = self._require_memory_record(key)

        candidate = self._mapper.memory_to_entity(record)
        try:
            existing = self._knowledge_graph.get_entity(candidate.id)
        except EntityNotFoundError:
            existing = None

        final_entity = candidate if existing is None else self._mapper.update_entity(existing, record)

        if existing is not None:
            # Cascades away every Relationship referencing the prior
            # Entity - see the module docstring's Synchronization
            # Semantics note.
            self._knowledge_graph.remove_entity(existing.id)

        try:
            self._knowledge_graph.add_entity(final_entity)
        except KnowledgeGraphError as error:
            self._failed[key] = str(error)
            self._synchronized.pop(key, None)
            self._publish(
                EventType.MEMORY_MAPPING_FAILED,
                {"key": key, "reason": str(error)},
            )
            raise MemoryMappingError(
                f"Failed to synchronize memory {key!r}: {error}"
            ) from error

        self._synchronized[key] = final_entity.id
        self._failed.pop(key, None)
        self._publish(
            EventType.MEMORY_SYNCHRONIZED,
            {"key": key, "entity_id": final_entity.id},
        )

        # Relationships are best-effort: one failed reference does not
        # undo the Entity sync that already succeeded above, and does
        # not stop the remaining relationships from being attempted.
        for relationship in self._mapper.memory_to_relationship(record):
            try:
                self._knowledge_graph.add_relationship(relationship)
            except KnowledgeGraphError as error:
                self._publish(
                    EventType.MEMORY_MAPPING_FAILED,
                    {
                        "key": key,
                        "relationship_id": relationship.id,
                        "target_entity_id": relationship.target_entity_id,
                        "reason": str(error),
                    },
                )

        return final_entity.id

    def remove_memory(self, key: str) -> None:
        self._require_running("remove_memory")
        entity_id = self._mapper.remove_entity(key)

        if key not in self._synchronized:
            raise MemoryNotSynchronizedError(
                f"Memory key {key!r} is not currently synchronized."
            )

        try:
            self._knowledge_graph.remove_entity(entity_id)
        except EntityNotFoundError:
            pass  # Already gone from the graph; bookkeeping still needs clearing.

        self._synchronized.pop(key, None)
        self._failed.pop(key, None)
        self._publish(
            EventType.MEMORY_DESYNCHRONIZED,
            {"key": key, "entity_id": entity_id},
        )

    def synchronize_all(self) -> Sequence[str]:
        self._require_running("synchronize_all")

        synchronized_keys = []
        for record in self._memory_service.list():
            try:
                self.synchronize_memory(record.key)
            except MemoryIntegrationError:
                # Already recorded in self._failed and published as
                # MEMORY_MAPPING_FAILED by synchronize_memory() itself;
                # one record's failure must not abort the batch.
                continue
            synchronized_keys.append(record.key)

        return tuple(synchronized_keys)

    # -- IMemoryIntegration: ungated (internal bookkeeping only) --------

    def synchronization_status(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "synchronized_count": len(self._synchronized),
                "synchronized_keys": tuple(self._synchronized),
                "failed_count": len(self._failed),
                "failed_keys": tuple(self._failed),
            }
        )

    def reset(self) -> None:
        """Clears only this service's own `self._synchronized`/
        `self._failed` bookkeeping. Neither the Memory Service's
        stored records nor the Knowledge Graph's Entities/Relationships
        are touched - "It owns no data itself.\""""
        self._synchronized.clear()
        self._failed.clear()

    # -- internal helpers -------------------------------------------------

    def _require_running(self, operation: str) -> None:
        if self._state != LifecycleState.RUNNING:
            raise InvalidMemoryIntegrationStateError(
                f"Cannot {operation}: MemoryIntegration is {self._state.name}, expected RUNNING."
            )

    def _require_memory_record(self, key: str):
        if not isinstance(key, str) or not key:
            raise InvalidMemoryRecordError("key must be a non-empty string.")
        try:
            return self._memory_service.get(key)
        except MemoryNotFoundError as error:
            raise InvalidMemoryRecordError(
                f"No memory record for key {key!r}."
            ) from error

    def _publish(self, event_type: EventType, payload: dict) -> None:
        self._event_bus.publish(
            Event(type=event_type, source="memory_integration", payload=payload)
        )
