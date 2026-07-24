"""
Public interface contract for the ArgusOS Event Bus.

Purpose:
    Define the Event Bus's public contract independently of any
    concrete implementation, per design/specifications/INTERFACES.md's
    "no subsystem may bypass another engine's published interface" and
    the Package 003 principle "interfaces before implementations".

    Other subsystems should depend on IEventBus, not on
    InMemoryEventBus, so the implementation can change without
    affecting callers.

Dependencies:
    argus.events.event (Event).
"""

from abc import ABC, abstractmethod
from typing import Callable

from argus.events.event import Event
from argus.events.event_types import EventType

# A handler receives the published Event and returns nothing. Handlers
# are plain callables; the Event Bus imposes no base class on them.
EventHandler = Callable[[Event], None]


class IEventBus(ABC):
    """
    Publish/subscribe messaging contract for ArgusOS.

    Purpose:
        Allow subsystems to communicate without depending on one
        another directly; every cross-subsystem interaction should be
        expressible as "publish an event" / "subscribe to an event
        type".
    """

    @abstractmethod
    def publish(self, event: Event) -> None:
        """
        Validate and deliver an event to all handlers subscribed to
        its type.

        Parameters:
            event: The Event to publish.

        Raises:
            EventValidationError: If the event is invalid.
        """
        raise NotImplementedError

    @abstractmethod
    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Register a handler to be invoked when an event of the given
        type is published.

        Parameters:
            event_type: The EventType to listen for.
            handler: A callable accepting a single Event argument.

        Raises:
            SubscriptionError: If the handler is not callable, or is
                already subscribed to this event type.
        """
        raise NotImplementedError

    @abstractmethod
    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Remove a previously registered handler.

        Parameters:
            event_type: The EventType the handler was subscribed to.
            handler: The handler to remove.

        Raises:
            SubscriptionError: If the handler is not currently
                subscribed to this event type.
        """
        raise NotImplementedError

    @abstractmethod
    def dispatch(self, event: Event) -> None:
        """
        Invoke every handler currently subscribed to the event's type,
        in registration order, without performing validation or
        logging.

        Parameters:
            event: The Event to deliver to subscribers.
        """
        raise NotImplementedError
