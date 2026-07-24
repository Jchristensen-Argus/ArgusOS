"""
KnowledgeService: CRUD orchestration for ArgusOS's persistent
knowledge store.

Purpose:
    Implement IKnowledgeService: maintain an in-memory, key-indexed
    view of every knowledge record, keep it synchronized with
    IKnowledgeStorage, and publish KnowledgeCreated / KnowledgeUpdated
    / KnowledgeDeleted events on the Event Bus, per
    factory/packages/006_KNOWLEDGE_SERVICE.md.

Responsibilities:
    - Load every category from storage at construction and build a
      single Dict[key, KnowledgeRecord] index (keys are globally
      unique across categories).
    - put / get / exists / delete / list / update, per
      IKnowledgeService.
    - Protect every write path (put, delete, update) with a
      threading.Lock. Reads (get, exists, list) remain unlocked, per
      the package's explicit v1 scope.
    - Publish KNOWLEDGE_CREATED / KNOWLEDGE_UPDATED / KNOWLEDGE_DELETED
      events after each successful write, once the write lock has
      been released.

Non-Responsibilities:
    - KnowledgeService does not decide how records are serialized or
      where they live on disk; that is IKnowledgeStorage's
      responsibility.
    - KnowledgeService does not implement IService / participate in
      the Lifecycle Manager's start/stop machinery in this package; it
      is registered with the Lifecycle Manager as a core service in
      LifecycleState.REGISTERED only, matching the other core services
      (see argus/bootstrap.py).

Dependencies:
    argus.events (Event, EventType, IEventBus), argus.knowledge
    (KnowledgeRecord, IKnowledgeService, IKnowledgeStorage,
    KnowledgeNotFoundError, DuplicateKnowledgeError).
"""

import threading
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence

from argus.events.event import Event
from argus.events.event_types import EventType
from argus.events.interfaces import IEventBus
from argus.knowledge.exceptions import (
    DuplicateKnowledgeError,
    KnowledgeError,
    KnowledgeNotFoundError,
)
from argus.knowledge.interfaces import IKnowledgeService, IKnowledgeStorage
from argus.knowledge.knowledge_record import KnowledgeRecord


class KnowledgeService(IKnowledgeService):
    """
    In-memory-indexed, storage-backed implementation of
    IKnowledgeService.

    Purpose:
        Give the rest of ArgusOS a single, simple place to durably
        remember facts (founder preferences, business data,
        architecture decisions, projects, tasks, conversation notes),
        grouped into categories, addressable by a globally unique key.

    Responsibilities:
        - Own the in-memory index and keep it consistent with the
          IKnowledgeStorage backend on every write.
        - Enforce key uniqueness (put) and existence (get/delete/update).
        - Publish knowledge lifecycle events on the Event Bus.

    Dependencies:
        An IKnowledgeStorage implementation and an IEventBus
        implementation, both injected by the caller (bootstrap.py).
    """

    def __init__(self, storage: IKnowledgeStorage, event_bus: IEventBus) -> None:
        self._storage = storage
        self._event_bus = event_bus
        self._write_lock = threading.Lock()
        self._index: Dict[str, KnowledgeRecord] = {}
        self._load_all()

    def _load_all(self) -> None:
        for category in self._storage.list_categories():
            for record in self._storage.load(category):
                self._index[record.key] = record

    def put(self, record: KnowledgeRecord) -> None:
        if not isinstance(record, KnowledgeRecord):
            raise KnowledgeError(f"put() requires a KnowledgeRecord, got {record!r}.")
        if not record.key:
            raise KnowledgeError("KnowledgeRecord.key must not be empty.")
        if not record.category:
            raise KnowledgeError("KnowledgeRecord.category must not be empty.")

        with self._write_lock:
            if record.key in self._index:
                raise DuplicateKnowledgeError(
                    f"Knowledge key {record.key!r} already exists."
                )
            self._index[record.key] = record
            self._persist_category(record.category)

        self._publish(EventType.KNOWLEDGE_CREATED, record)

    def get(self, key: str) -> KnowledgeRecord:
        record = self._index.get(key)
        if record is None:
            raise KnowledgeNotFoundError(f"No knowledge record for key {key!r}.")
        return record

    def exists(self, key: str) -> bool:
        return key in self._index

    def delete(self, key: str) -> None:
        with self._write_lock:
            record = self._index.get(key)
            if record is None:
                raise KnowledgeNotFoundError(f"No knowledge record for key {key!r}.")
            del self._index[key]
            self._persist_category(record.category)

        self._publish(EventType.KNOWLEDGE_DELETED, record)

    def list(self, category: Optional[str] = None) -> Sequence[KnowledgeRecord]:
        records = self._index.values()
        if category is not None:
            records = (record for record in records if record.category == category)
        return tuple(records)

    def update(self, key: str, value: Any) -> KnowledgeRecord:
        with self._write_lock:
            existing = self._index.get(key)
            if existing is None:
                raise KnowledgeNotFoundError(f"No knowledge record for key {key!r}.")

            updated = replace(
                existing,
                value=value,
                updated_at=datetime.now(timezone.utc),
                version=existing.version + 1,
            )
            self._index[key] = updated
            self._persist_category(updated.category)

        self._publish(EventType.KNOWLEDGE_UPDATED, updated)
        return updated

    def _persist_category(self, category: str) -> None:
        # Must be called while holding self._write_lock. Rebuilds the
        # full record list for `category` from the in-memory index and
        # hands it to storage.save(), which performs the atomic write.
        # O(n) in the number of records in the category; deliberately
        # simple, per the package's v1 scope (see module docstring).
        records = [record for record in self._index.values() if record.category == category]
        self._storage.save(category, records)

    def _publish(self, event_type: EventType, record: KnowledgeRecord) -> None:
        # Published after the write lock is released, so a handler
        # that calls back into KnowledgeService (e.g. get(), or even
        # another put()/update()/delete()) can never deadlock on
        # self._write_lock, which is not reentrant.
        self._event_bus.publish(
            Event(
                type=event_type,
                source="knowledge_service",
                payload={
                    "key": record.key,
                    "category": record.category,
                    "version": record.version,
                },
            )
        )
