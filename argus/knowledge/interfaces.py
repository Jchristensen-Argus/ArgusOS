"""
Public interface contracts for the ArgusOS Knowledge Service.

Purpose:
    Define the abstract contracts other modules depend on
    (IKnowledgeService, IKnowledgeStorage), per
    factory/packages/006_KNOWLEDGE_SERVICE.md, so callers depend on
    behavior rather than a concrete implementation.

Responsibilities:
    - IKnowledgeStorage: the persistence abstraction KnowledgeService
      depends on, so the backing store (JSON today; SQLite or
      something else later) can change without touching
      KnowledgeService.
    - IKnowledgeService: the CRUD contract ArgusOS subsystems use to
      read and write persistent knowledge.

Non-Responsibilities:
    - Neither interface implements any behavior; see
      argus.knowledge.storage.JSONKnowledgeStorage and
      argus.knowledge.knowledge_service.KnowledgeService.

Dependencies:
    argus.knowledge.knowledge_record (KnowledgeRecord).
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Sequence

from argus.knowledge.knowledge_record import KnowledgeRecord


class IKnowledgeStorage(ABC):
    """
    Persistence contract for knowledge records, grouped by category.

    Purpose:
        Let KnowledgeService read and write knowledge records without
        knowing whether they live in JSON files, a database, or
        anything else.
    """

    @abstractmethod
    def list_categories(self) -> Sequence[str]:
        """Return the names of every known category (e.g. discovered
        from files on disk), in a deterministic order."""

    @abstractmethod
    def load(self, category: str) -> Sequence[KnowledgeRecord]:
        """Return every KnowledgeRecord stored under `category`. If the
        category has no stored records, return an empty sequence."""

    @abstractmethod
    def save(self, category: str, records: Sequence[KnowledgeRecord]) -> None:
        """Replace everything stored under `category` with exactly
        `records`."""


class IKnowledgeService(ABC):
    """
    CRUD contract for ArgusOS's authoritative long-lived knowledge
    store.

    Purpose:
        Let ArgusOS subsystems create, read, update, and delete
        knowledge records by key, without knowing how or where those
        records are persisted.
    """

    @abstractmethod
    def put(self, record: KnowledgeRecord) -> None:
        """Store a new record. Raises DuplicateKnowledgeError if
        record.key is already present."""

    @abstractmethod
    def get(self, key: str) -> KnowledgeRecord:
        """Return the record for `key`. Raises KnowledgeNotFoundError
        if no such record exists."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return True if a record for `key` exists."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove the record for `key`. Raises KnowledgeNotFoundError
        if no such record exists."""

    @abstractmethod
    def list(self, category: Optional[str] = None) -> Sequence[KnowledgeRecord]:
        """Return every known record, or only those in `category` if
        given."""

    @abstractmethod
    def update(self, key: str, value: Any) -> KnowledgeRecord:
        """Replace the value of the record for `key`, bump its
        version, and return the new record. Raises
        KnowledgeNotFoundError if no such record exists."""
