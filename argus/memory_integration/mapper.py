"""
MemoryMapper: pure translation between Memory Records and Knowledge
Graph Entities/Relationships.

Purpose:
    Implement the four translation operations Package 019's own
    Memory Mapper section names - memory_to_entity(),
    memory_to_relationship(), update_entity(), remove_entity() - and
    nothing else. "The mapper performs only translation. No business
    logic." Every method here is a pure, side-effect-free function:
    none of them call argus.memory or argus.knowledge_graph - they
    only construct and return the argus.knowledge_graph value objects
    (Entity, Relationship) or plain identifiers that
    MemoryIntegration (argus/memory_integration/integration.py) then
    applies to a live IKnowledgeGraph. This module has no dependency
    on IMemoryService or IKnowledgeGraph, only on the value objects
    both packages already define.

Deterministic Entity Id Scheme:
    Every Entity this mapper produces for a given memory `key` is
    given the id `f"memory:{key}"` - a pure, deterministic function of
    the key alone. This is the mechanism that satisfies Package 019's
    "prevent duplicate graph entities" requirement without any
    separate lookup table: the same memory key always maps to the
    same graph Entity id, so re-synchronizing an already-synchronized
    key naturally resolves to the same Entity rather than creating a
    second one. It is also what lets remove_entity() (below) compute
    the id to remove directly from a bare key string, without first
    needing to fetch the (possibly already-deleted) MemoryRecord.

Relationship Convention - `related_keys`:
    argus.memory.memory_record.MemoryRecord has no relationship
    concept of its own - `value` is untyped `Any`. Rather than
    attempting any form of inference (explicitly forbidden - "shall
    NOT perform graph reasoning"), memory_to_relationship() recognizes
    exactly one simple, mechanical convention: if `record.value` is a
    Mapping containing a `"related_keys"` entry whose value is an
    iterable of strings, each string is treated as another memory key
    this record is related to, and translated into one Relationship
    (relationship_type `"related_to"`) per entry. A record whose
    `value` is not a Mapping, or has no `"related_keys"` entry, or
    whose `"related_keys"` entry is not an iterable of strings,
    produces no Relationships at all - this is the default, common
    case, not an error condition.

Responsibilities:
    - memory_to_entity(record): translate one MemoryRecord into a
      brand-new Entity.
    - memory_to_relationship(record): translate one MemoryRecord's
      `related_keys` convention (if present) into zero or more
      Relationships.
    - update_entity(existing, record): given an Entity previously
      produced by this mapper and a possibly-changed MemoryRecord for
      the same key, produce the Entity's updated form (same id,
      refreshed attributes).
    - remove_entity(key): translate a bare memory key into the graph
      Entity id that represents it, for the caller to pass to
      IKnowledgeGraph.remove_entity().

Non-Responsibilities:
    - This module never calls IMemoryService or IKnowledgeGraph - see
      argus.memory_integration.integration.MemoryIntegration for all
      orchestration.
    - This module performs no validation beyond confirming its inputs
      are the expected types - it is not responsible for checking
      whether a referenced `related_keys` entry actually exists as a
      registered Entity (that is IKnowledgeGraph.add_relationship()'s
      own existing invalid-reference check, surfaced to
      MemoryIntegration's caller as MEMORY_MAPPING_FAILED).

Dependencies:
    argus.knowledge_graph (Entity, Relationship),
    argus.memory.memory_record (MemoryRecord),
    argus.memory_integration.exceptions (InvalidMemoryRecordError).
"""

from typing import Any, Mapping, Sequence

from argus.knowledge_graph.entity import Entity
from argus.knowledge_graph.relationship import Relationship
from argus.memory.memory_record import MemoryRecord
from argus.memory_integration.exceptions import InvalidMemoryRecordError

_ENTITY_TYPE = "memory"
_RELATIONSHIP_TYPE = "related_to"


class MemoryMapper:
    """
    Pure translation between MemoryRecords and Knowledge Graph
    Entities/Relationships. Holds no state and calls no other
    service - see the module docstring for the full design rationale.
    """

    def memory_to_entity(self, record: MemoryRecord) -> Entity:
        """Translate a MemoryRecord into a brand-new Entity, per the
        module's own Deterministic Entity Id Scheme."""
        self._require_record(record)
        return Entity(
            id=self._entity_id(record.key),
            entity_type=_ENTITY_TYPE,
            name=record.key,
            attributes=self._attributes(record),
        )

    def memory_to_relationship(self, record: MemoryRecord) -> Sequence[Relationship]:
        """Translate a MemoryRecord's `related_keys` convention (if
        present) into zero or more Relationships. See the module's
        own Relationship Convention note."""
        self._require_record(record)

        related_keys = self._related_keys(record.value)
        source_id = self._entity_id(record.key)
        return tuple(
            Relationship(
                source_entity_id=source_id,
                target_entity_id=self._entity_id(other_key),
                relationship_type=_RELATIONSHIP_TYPE,
                attributes={"source_key": record.key, "target_key": other_key},
            )
            for other_key in related_keys
        )

    def update_entity(self, existing: Entity, record: MemoryRecord) -> Entity:
        """Given an Entity previously produced by this mapper and a
        possibly-changed MemoryRecord for the same key, produce the
        Entity's updated form: the same `id`, with `attributes`
        refreshed from the current record. Unlike memory_to_entity(),
        which always derives `id` fresh from `record.key`,
        update_entity() explicitly preserves `existing.id` - a
        deliberate defensive choice, should this mapper's id-
        derivation scheme ever change in a future package."""
        self._require_record(record)
        if not isinstance(existing, Entity):
            raise InvalidMemoryRecordError(
                f"update_entity() requires an Entity, got {existing!r}."
            )
        return Entity(
            id=existing.id,
            entity_type=_ENTITY_TYPE,
            name=record.key,
            attributes=self._attributes(record),
        )

    def remove_entity(self, key: str) -> str:
        """Translate a bare memory key into the graph Entity id that
        represents it - the id the caller should pass to
        IKnowledgeGraph.remove_entity()."""
        if not isinstance(key, str) or not key:
            raise InvalidMemoryRecordError("remove_entity() requires a non-empty key string.")
        return self._entity_id(key)

    # -- internal helpers -------------------------------------------------

    @staticmethod
    def _entity_id(key: str) -> str:
        return f"memory:{key}"

    @staticmethod
    def _attributes(record: MemoryRecord) -> Mapping[str, Any]:
        return {
            "value": record.value,
            "memory_id": record.id,
            "version": record.version,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
            "expires_at": record.expires_at,
        }

    @staticmethod
    def _related_keys(value: Any) -> Sequence[str]:
        if not isinstance(value, Mapping):
            return ()
        candidate = value.get("related_keys")
        if candidate is None or isinstance(candidate, (str, bytes)):
            return ()
        try:
            return tuple(key for key in candidate if isinstance(key, str))
        except TypeError:
            return ()

    @staticmethod
    def _require_record(record: MemoryRecord) -> None:
        if not isinstance(record, MemoryRecord):
            raise InvalidMemoryRecordError(
                f"MemoryMapper requires a MemoryRecord, got {record!r}."
            )
        if not record.key:
            raise InvalidMemoryRecordError("MemoryRecord.key must be non-empty.")
