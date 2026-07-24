"""
KnowledgeRecord for the ArgusOS Knowledge Service.

Purpose:
    Represent a single, immutable fact stored in ArgusOS's persistent
    knowledge store, per factory/packages/006_KNOWLEDGE_SERVICE.md.

Responsibilities:
    - Hold a record's identity (id), classification (category), the
      globally-unique lookup key, the stored value, timing
      (created_at/updated_at), and a version counter.
    - Guarantee immutability: once constructed, a KnowledgeRecord
      cannot be changed by anything that receives it. Updates are
      performed by constructing a new KnowledgeRecord (see
      KnowledgeService.update, which uses dataclasses.replace).

Non-Responsibilities:
    - KnowledgeRecord does not validate, persist, or index itself.
      That is IKnowledgeStorage's and KnowledgeService's
      responsibility.
    - KnowledgeRecord does not deep-freeze `value`. Only the record's
      own fields are frozen (dataclass(frozen=True)); if a caller
      stores a mutable object (e.g. a dict) as `value` and keeps a
      reference to it, mutating that object in place is not prevented.
      This mirrors the "intentionally simple, v1" scope of this
      package.

Dependencies:
    None (standard library only).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class KnowledgeRecord:
    """
    An immutable record of one fact in ArgusOS's knowledge store.

    Purpose:
        Carry a knowledge entry's identity and value through the
        Knowledge Service and its storage layer without exposing any
        way to mutate it after construction.

    Responsibilities:
        - Store category, key, value, id, created_at, updated_at, and
          version.
        - Auto-generate `id`, `created_at`, and `updated_at` when not
          supplied, and default `version` to 1.

    Dependencies:
        None.
    """

    category: str
    key: str
    value: Any
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1
