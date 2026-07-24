"""
MemoryRecord for the ArgusOS Memory Service.

Purpose:
    Represent a single, immutable item of working memory, per
    factory/packages/007_MEMORY_SERVICE.md and
    design/specifications/MEMORY.md.

Responsibilities:
    - Hold a record's identity (id), the globally-unique lookup key,
      the stored value, timing (created_at/updated_at), an optional
      expiry (expires_at), and a version counter.
    - Guarantee immutability: once constructed, a MemoryRecord cannot
      be changed by anything that receives it. Updates are performed
      by constructing a new MemoryRecord (see MemoryService.update,
      which uses dataclasses.replace).

Non-Responsibilities:
    - MemoryRecord does not decide whether it has expired; that is a
      read-time judgment made by IKnowledgeStorage's caller
      (MemoryService), by comparing expires_at to the current time.
      MemoryRecord only stores the timestamp.
    - MemoryRecord does not validate, persist, or index itself. That
      is IMemoryStorage's and MemoryService's responsibility.
    - Like Package 006's KnowledgeRecord, MemoryRecord does not
      deep-freeze `value`; only the record's own fields are immutable.

Dependencies:
    None (standard library only).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass(frozen=True)
class MemoryRecord:
    """
    An immutable record of one item of ArgusOS's working memory.

    Purpose:
        Carry a memory entry's identity, value, and optional expiry
        through the Memory Service and its storage layer without
        exposing any way to mutate it after construction.

    Responsibilities:
        - Store key, value, id, created_at, updated_at, expires_at,
          and version.
        - Auto-generate `id`, `created_at`, and `updated_at` when not
          supplied, and default `version` to 1 and `expires_at` to
          None (never expires).

    Dependencies:
        None.
    """

    key: str
    value: Any
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    version: int = 1

    def is_expired(self, *, now: Optional[datetime] = None) -> bool:
        """
        Return True if this record's expires_at is set and is at or
        before `now` (defaults to the current UTC time).

        A record with expires_at=None never expires.
        """
        if self.expires_at is None:
            return False
        reference_time = now if now is not None else datetime.now(timezone.utc)
        return self.expires_at <= reference_time
