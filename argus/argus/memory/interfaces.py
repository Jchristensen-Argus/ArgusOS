"""
Public interface contracts for the ArgusOS Memory Service.

Purpose:
    Define the abstract contracts other modules depend on
    (IMemoryService, IMemoryStorage), per
    factory/packages/007_MEMORY_SERVICE.md and
    design/specifications/MEMORY.md ("Public Interfaces: Store Memory,
    Retrieve Memory, Update Memory, Delete Memory, Search Memory, List
    Memory"), so callers depend on behavior rather than a concrete
    implementation.

Responsibilities:
    - IMemoryStorage: the persistence abstraction MemoryService
      depends on, so the backing store (a single JSON file today;
      something else later) can change without touching MemoryService.
    - IMemoryService: the CRUD-plus-expiry contract ArgusOS subsystems
      use to store and retrieve short-term working memory.

Non-Responsibilities:
    - Neither interface implements any behavior; see
      argus.memory.storage.JSONMemoryStorage and
      argus.memory.memory_service.MemoryService.

Dependencies:
    argus.memory.memory_record (MemoryRecord).
"""

from abc import ABC, abstractmethod
from typing import Any, Sequence

from argus.memory.memory_record import MemoryRecord


class IMemoryStorage(ABC):
    """
    Persistence contract for memory records.

    Purpose:
        Let MemoryService read and write memory records without
        knowing whether they live in a JSON file, a database, or
        anything else.
    """

    @abstractmethod
    def load(self) -> Sequence[MemoryRecord]:
        """Return every MemoryRecord currently stored, expired or not.
        If nothing is stored, return an empty sequence."""

    @abstractmethod
    def save(self, records: Sequence[MemoryRecord]) -> None:
        """Replace everything in storage with exactly `records`."""


class IMemoryService(ABC):
    """
    CRUD-plus-expiry contract for ArgusOS's short-term working memory.

    Purpose:
        Let ArgusOS subsystems (eventually Atlas and Cortex, per
        design/specifications/MEMORY.md's Inputs) create, read,
        update, delete, and search working memory by key, with each
        record optionally self-expiring, without knowing how or where
        those records are persisted.
    """

    @abstractmethod
    def put(self, record: MemoryRecord) -> None:
        """Store a new record. Raises DuplicateMemoryError if
        record.key is already present (even if the existing record
        has since expired but not yet been purged)."""

    @abstractmethod
    def get(self, key: str) -> MemoryRecord:
        """Return the record for `key`. Raises MemoryNotFoundError if
        no such record exists, or if it exists but has expired."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return True if a record for `key` exists and has not
        expired."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove the record for `key`. Raises MemoryNotFoundError if
        no such (non-expired) record exists."""

    @abstractmethod
    def update(self, key: str, value: Any) -> MemoryRecord:
        """Replace the value of the record for `key`, bump its
        version, and return the new record. Raises
        MemoryNotFoundError if no such (non-expired) record exists."""

    @abstractmethod
    def list(self) -> Sequence[MemoryRecord]:
        """Return every non-expired record currently stored."""

    @abstractmethod
    def search(self, query: str) -> Sequence[MemoryRecord]:
        """Return every non-expired record whose key contains `query`
        (case-insensitive substring match). This is intentionally a
        simple substring search, not semantic search, which is listed
        as a Future Enhancement for Atlas, not in scope here."""

    @abstractmethod
    def purge_expired(self) -> int:
        """Permanently remove every expired record from storage.
        Returns the number of records removed. Expired records are
        already treated as absent by get/exists/list/search before
        this is called; this is the only operation that physically
        deletes them."""
