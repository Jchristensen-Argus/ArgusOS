"""
The ConversationSession value object for the ArgusOS Conversation
Manager.

Purpose:
    Represent a single, immutable snapshot of one conversation's
    identity, progress, and full message history, per
    factory/packages/011_CONVERSATION_MANAGER.md.

Responsibilities:
    - Auto-generate `id` and `created_at` when not supplied. Default
      `updated_at` to the same value as `created_at` at construction
      time.
    - Default `state` to ConversationState.NEW, `metadata` to an empty
      mapping, and `messages` to an empty sequence.
    - Guarantee immutability (frozen dataclass) and prevent mutation
      of the `messages` sequence (wrapped in a tuple) or `metadata`
      mapping (wrapped in MappingProxyType) after construction.

Non-Responsibilities:
    - This module implements no transition logic or message-handling
      behavior. ConversationManager (argus/conversation/manager.py) is
      the only component that advances a session's state or appends
      to its messages - it does so by constructing new
      ConversationSession instances via dataclasses.replace, never by
      mutating an existing one.

Dependencies:
    argus.conversation.message (ConversationMessage),
    argus.conversation.state (ConversationState).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from argus.conversation.message import ConversationMessage
from argus.conversation.state import ConversationState


@dataclass(frozen=True)
class ConversationSession:
    """
    An immutable record of a single conversation: its identity, its
    current state, and its full message history so far.

    Purpose:
        Represent "what has been said" (messages) and "where things
        stand" (state) as one consistent, immutable snapshot.

    Dependencies:
        None.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    state: ConversationState = ConversationState.NEW
    metadata: Mapping[str, Any] = field(default_factory=dict)
    messages: Sequence[ConversationMessage] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        # Frozen dataclasses require object.__setattr__ to set fields,
        # including during __post_init__. See Workflow.__post_init__
        # (Package 010) for the identical pattern.
        object.__setattr__(self, "messages", tuple(self.messages))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
