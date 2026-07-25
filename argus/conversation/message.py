"""
The ConversationMessage value object and ConversationRole enum for the
ArgusOS Conversation Manager.

Purpose:
    Represent a single, immutable turn in a conversation - who said
    it, when, and what - per
    factory/packages/011_CONVERSATION_MANAGER.md.

Responsibilities:
    - ConversationRole: enumerate USER, ASSISTANT, SYSTEM as the only
      valid message roles.
    - ConversationMessage: auto-generate `id` and `timestamp` when not
      supplied. Guarantee immutability (frozen dataclass) and prevent
      mutation of the metadata mapping after construction.

Non-Responsibilities:
    - This module implements no conversation logic. ConversationManager
      (argus/conversation/manager.py) is the only component that
      constructs ConversationMessage instances during normal operation.

Dependencies:
    None.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class ConversationRole(Enum):
    """The only valid roles a ConversationMessage's author may have."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass(frozen=True)
class ConversationMessage:
    """
    An immutable record of a single message within a
    ConversationSession.

    Purpose:
        Capture who sent a message, when, and what it said, as one
        consistent, immutable snapshot.

    Responsibilities:
        - Auto-generate `id` and `timestamp` when not supplied.
        - Default `metadata` to an empty mapping.
        - Reject accidental mutation after construction (frozen
          dataclass) and prevent mutation of `metadata` (wrapped in
          MappingProxyType).

    Dependencies:
        None.
    """

    role: ConversationRole
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
