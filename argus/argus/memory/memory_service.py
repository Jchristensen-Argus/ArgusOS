"""
MemoryService: expiry-aware CRUD orchestration for ArgusOS's
short-term working memory.

Purpose:
    Implement IMemoryService: maintain an in-memory, key-indexed view
    of every memory record, keep it synchronized with IMemoryStorage,
    treat expired records as absent on every read path, and publish
    EventType.MEMORY_UPDATED on the Event Bus after each successful
    mutation, per factory/packages/007_MEMORY_SERVICE.md.

Responsibilities:
    - Load every record from storage at construction and build a
      single Dict[key, MemoryRecord] index.
    - put / get / exists / delete / update / list / search /
      purge_expired, per IMemoryService.
    - Protect every write path (put, delete, update, purge_expired)
      with a threading.Lock. Reads (get, exists, list, search) remain
      unlocked and never mutate storage, matching the read/write split
      established by Package 006's KnowledgeService.
    - Treat any record whose expires_at has passed as invisible to
      every read path, without physically removing it. Only
      purge_expired() performs the physical removal - there is no
      background sweep thread, per this package's explicit "no
      timers, no background workers" scope (see
      factory/packages/007_MEMORY_SERVICE.md, Out of Scope).
    - Publish EventType.MEMORY_UPDATED after each successful write,
      once the write lock has been released, with an "operation"
      field in the payload distinguishing created / updated / deleted
      / purged.

Non-Responsibilities:
    - MemoryService does not decide how records are serialized or
      where they live on disk; that is IMemoryStorage's
      responsibility.
    - MemoryService does not implement IService in this package; see
      the Out of Scope section of factory/packages/007_MEMORY_SERVICE.md
      for why adopting IService is deliberately deferred.
    - MemoryService does not perform semantic search. search() is a
      simple case-insensitive substring match on key.

Dependencies:
    argus.events (Event, EventType, IEventBus), argus.memory
    (MemoryRecord, IMemoryService, IMemoryStorage,
    MemoryNotFoundError, DuplicateMemoryError, MemoryServiceError).
"""

import threading
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence

from argus.events.event import Event
from argus.events.event_types import EventType
from argus.events.interfaces import IEventBus
from argus.memory.exceptions import (
    DuplicateMemoryError,
    MemoryNotFoundError,
    MemoryServiceError,
)
from argus.memory.interfaces import IMemoryService, IMemoryStorage
from argus.memory.memory_record import MemoryRecord


class MemoryService(IMemoryService):
    """
    In-memory-indexed, storage-backed implementation of
    IMemoryService.

    Purpose:
        Give ArgusOS's reasoning-facing subsystems (eventually Atlas
        and Cortex) a place to remember short-term, optionally
        self-expiring information, distinct from Package 006's
        Knowledge Service, which has no expiry concept and is scoped
        to durable, human-curated facts.

    Responsibilities:
        - Own the in-memory index and keep it consistent with the
          IMemoryStorage backend on every write.
        - Enforce key uniqueness (put) and existence (get / delete /
          update), treating expired records as nonexistent.
        - Publish memory lifecycle events on the Event Bus.

    Dependencies:
        An IMemoryStorage implementation and an IEventBus
        implementation, both injected by the caller (bootstrap.py).
    """

    def __init__(self, storage: IMemoryStorage, event_bus: IEventBus) -> None:
        self._storage = storage
        self._event_bus = event_bus
        self._write_lock = threading.Lock()
        self._index: Dict[str, MemoryRecord] = {}
        self._load_all()

    def _load_all(self) -> None:
        for record in self._storage.load():
            self._index[record.key] = record

    def put(self, record: MemoryRecord) -> None:
        if not isinstance(record, MemoryRecord):
            raise MemoryServiceError(f"put() requires a MemoryRecord, got {record!r}.")
        if not record.key:
            raise MemoryServiceError("MemoryRecord.key must not be empty.")

        with self._write_lock:
            if record.key in self._index:
                raise DuplicateMemoryError(f"Memory key {record.key!r} already exists.")
            self._index[record.key] = record
            self._persist()

        self._publish("created", record)

    def get(self, key: str) -> MemoryRecord:
        record = self._live_record(key)
        if record is None:
            raise MemoryNotFoundError(f"No memory record for key {key!r}.")
        return record

    def exists(self, key: str) -> bool:
        return self._live_record(key) is not None

    def delete(self, key: str) -> None:
        with self._write_lock:
            record = self._live_record(key)
            if record is None:
                raise MemoryNotFoundError(f"No memory record for key {key!r}.")
            del self._index[key]
            self._persist()

        self._publish("deleted", record)

    def update(self, key: str, value: Any) -> MemoryRecord:
        with self._write_lock:
            existing = self._live_record(key)
            if existing is None:
                raise MemoryNotFoundError(f"No memory record for key {key!r}.")

            updated = replace(
                existing,
                value=value,
                updated_at=datetime.now(timezone.utc),
                version=existing.version + 1,
            )
            self._index[key] = updated
            self._persist()

        self._publish("updated", updated)
        return updated

    def list(self) -> Sequence[MemoryRecord]:
        now = datetime.now(timezone.utc)
        return tuple(
            record for record in self._index.values() if not record.is_expired(now=now)
        )

    def search(self, query: str) -> Sequence[MemoryRecord]:
        needle = query.lower()
        return tuple(record for record in self.list() if needle in record.key.lower())

    def purge_expired(self) -> int:
        with self._write_lock:
            now = datetime.now(timezone.utc)
            expired_keys = [
                key for key, record in self._index.items() if record.is_expired(now=now)
            ]
            expired_records = [self._index[key] for key in expired_keys]
            for key in expired_keys:
                del self._index[key]
            if expired_keys:
                self._persist()

        for record in expired_records:
            self._publish("purged", record)

        return len(expired_records)

    def _live_record(self, key: str) -> Optional[MemoryRecord]:
        # Not called while holding self._write_lock: reads never
        # mutate storage, per this package's explicit lazy-expiry
        # design (see module docstring).
        record = self._index.get(key)
        if record is None or record.is_expired():
            return None
        return record

    def _persist(self) -> None:
        # Must be called while holding self._write_lock. Rebuilds the
        # full record list (including still-expired-but-not-yet-purged
        # records, which are storage's concern, not a write-path
        # concern) and hands it to storage.save(), which performs the
        # atomic write.
        self._storage.save(list(self._index.values()))

    def _publish(self, operation: str, record: MemoryRecord) -> None:
        # Published after the write lock is released, so a handler
        # that calls back into MemoryService can never deadlock on
        # self._write_lock, which is not reentrant. Mirrors Package
        # 006's KnowledgeService._publish.
        self._event_bus.publish(
            Event(
                type=EventType.MEMORY_UPDATED,
                source="memory_service",
                payload={
                    "operation": operation,
                    "key": record.key,
                    "version": record.version,
                },
            )
        )
