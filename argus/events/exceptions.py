"""
Exceptions raised by the ArgusOS Event Bus.

Purpose:
    Give callers explicit, catchable failure modes for invalid events
    and invalid subscription operations, per the coding standard's
    "explicit exceptions instead of silent failures" and
    factory/packages/003_EVENT_BUS.md.

Dependencies:
    None.
"""


class EventValidationError(Exception):
    """Raised when an Event (or the value passed as one) is invalid:
    missing, of the wrong type, or missing a required field such as
    `source`."""


class SubscriptionError(Exception):
    """Raised when a subscribe/unsubscribe operation is invalid: the
    handler is not callable, the handler is already subscribed to the
    event type (duplicate subscription), or the handler was not
    subscribed to the event type (unsubscribe of an unknown
    handler)."""
