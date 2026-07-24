"""
Exceptions raised by the ArgusOS Service Registry.

Purpose:
    Give callers explicit, catchable failure modes for invalid
    registration and lookup operations, per the coding standard's
    "explicit exceptions instead of silent failures" and
    factory/packages/004_SERVICE_REGISTRY.md.

Responsibilities:
    - Provide two distinct, unambiguous exception types so callers can
      tell a duplicate/invalid registration apart from a lookup that
      found nothing.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do not
      log, retry, or recover.

Dependencies:
    None.
"""


class ServiceRegistrationError(Exception):
    """Raised when a service cannot be registered: the descriptor is
    invalid, or a service is already registered under the same
    name."""


class ServiceNotFoundError(Exception):
    """Raised when an operation references a service name that is not
    currently registered (resolve, unregister, or any other lookup by
    name)."""
