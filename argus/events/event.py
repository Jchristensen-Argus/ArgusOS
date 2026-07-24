"""
The Event value object for the ArgusOS Event Bus.

Purpose:
    Represent a single, immutable fact that has occurred somewhere in
    ArgusOS, carried through the Event Bus to any interested
    subscribers, per factory/packages/003_EVENT_BUS.md.

Responsibilities:
    - Hold event identity (id), classification (type), origin (source),
      timing (timestamp), and payload/metadata.
    - Guarantee immutability: once constructed, an Event cannot be
      changed by anything that receives it.

Non-Responsibilities:
    - Event does not know how it is delivered, stored, or logged.
      That is the Event Bus's responsibility.

Dependencies:
    argus.events.event_types (EventPriority, EventType).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from argus.events.event_types import EventPriority, EventType


@dataclass(frozen=True)
class Event:
    """
    An immutable record of something that happened in ArgusOS.

    Purpose:
        Carry a single occurrence through the Event Bus to subscribers,
        without exposing any way for a subscriber to mutate it.

    Responsibilities:
        - Auto-generate `id` and `timestamp` when not supplied.
        - Default `payload` and `metadata` to empty mappings.
        - Reject accidental mutation after construction (frozen
          dataclass) and prevent mutation of the payload/metadata
          mappings themselves (wrapped in MappingProxyType), per the
          Event Bus's "never mutate events" responsibility.

    Dependencies:
        None.
    """

    type: EventType
    source: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL

    def __post_init__(self) -> None:
        # Frozen dataclasses require object.__setattr__ to set fields,
        # including during __post_init__. This makes the payload and
        # metadata mappings themselves read-only, not just the
        # attribute reference, so a handler cannot mutate event.payload
        # in place.
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
