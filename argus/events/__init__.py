"""
ArgusOS Event Bus package.

Purpose:
    Public entry point for the Event Bus subsystem. Re-exports the
    symbols other modules need (Event, event enums, the IEventBus
    contract, the InMemoryEventBus implementation, and the Event Bus
    exceptions) so callers can depend on `argus.events` rather than
    reaching into individual submodules.

Dependencies:
    None beyond the submodules it re-exports.
"""

from argus.events.event import Event
from argus.events.event_bus import InMemoryEventBus
from argus.events.event_types import EventPriority, EventType
from argus.events.exceptions import EventValidationError, SubscriptionError
from argus.events.interfaces import EventHandler, IEventBus

__all__ = [
    "Event",
    "EventPriority",
    "EventType",
    "IEventBus",
    "EventHandler",
    "InMemoryEventBus",
    "EventValidationError",
    "SubscriptionError",
]
