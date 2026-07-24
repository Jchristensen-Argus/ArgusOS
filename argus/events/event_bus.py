"""
In-memory implementation of the ArgusOS Event Bus.

Purpose:
    Provide the single, synchronous publish/subscribe communication
    backbone for ArgusOS, per factory/packages/003_EVENT_BUS.md.

Responsibilities:
    - Maintain subscriptions per event type, in registration order.
    - Validate events and handlers explicitly; never fail silently.
    - Dispatch events to subscribed handlers synchronously.
    - Log structured details of every publish operation.
    - Never mutate the events it carries.

Non-Responsibilities (explicitly out of scope for this package):
    AsyncIO, threads, queues, external brokers (Redis/RabbitMQ/Kafka),
    event persistence, replay, distributed messaging, priority-based
    scheduling, middleware, event filtering, network transport,
    performance optimization.

Dependencies:
    A standard library Logger, injected by the caller (bootstrap.py).
    The Event Bus never constructs its own logger, per the "no hidden
    dependencies" principle.
"""

import logging
import time
from typing import Dict, List

from argus.events.event import Event
from argus.events.event_types import EventType
from argus.events.exceptions import EventValidationError, SubscriptionError
from argus.events.interfaces import EventHandler, IEventBus


class InMemoryEventBus(IEventBus):
    """
    Synchronous, in-process publish/subscribe Event Bus.

    Purpose:
        Let ArgusOS subsystems communicate without depending on one
        another directly.

    Responsibilities:
        - subscribe / unsubscribe handlers per EventType.
        - publish: validate an event, log the operation, then dispatch it.
        - dispatch: invoke subscribed handlers, in registration order.

    Dependencies:
        A logging.Logger, supplied by the caller.
    """

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._subscribers: Dict[EventType, List[EventHandler]] = {}

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        if not isinstance(event_type, EventType):
            raise SubscriptionError(
                f"Cannot subscribe: '{event_type}' is not a valid EventType."
            )
        if not callable(handler):
            raise SubscriptionError(
                f"Cannot subscribe: handler {handler!r} is not callable."
            )

        handlers = self._subscribers.setdefault(event_type, [])
        if handler in handlers:
            raise SubscriptionError(
                f"Handler {handler!r} is already subscribed to {event_type}."
            )
        handlers.append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        handlers = self._subscribers.get(event_type, [])
        if handler not in handlers:
            raise SubscriptionError(
                f"Handler {handler!r} is not subscribed to {event_type}."
            )
        handlers.remove(handler)

    def publish(self, event: Event) -> None:
        self._validate_event(event)

        handler_count = len(self._subscribers.get(event.type, []))

        start = time.monotonic()
        self.dispatch(event)
        duration_ms = (time.monotonic() - start) * 1000

        self._logger.info(
            "Event published: type=%s source=%s priority=%s handlers=%d duration_ms=%.3f",
            event.type.name,
            event.source,
            event.priority.name,
            handler_count,
            duration_ms,
        )

    def dispatch(self, event: Event) -> None:
        # Copy the handler list before iterating: a handler that
        # subscribes or unsubscribes during dispatch must not change
        # the list currently being iterated, and must never see the
        # event mutated (Event is immutable, so that half is
        # guaranteed by construction).
        handlers = list(self._subscribers.get(event.type, []))
        for handler in handlers:
            handler(event)

    @staticmethod
    def _validate_event(event: Event) -> None:
        if event is None:
            raise EventValidationError("Event must not be None.")
        if not isinstance(event.type, EventType):
            raise EventValidationError(
                f"Event.type must be a valid EventType, got {event.type!r}."
            )
        if not event.source:
            raise EventValidationError("Event.source must not be empty.")
