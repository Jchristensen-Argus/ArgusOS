"""
Exceptions raised by the ArgusOS Lifecycle Manager.

Purpose:
    Give callers explicit, catchable failure modes for lifecycle
    operations, per the coding standard's "explicit exceptions instead
    of silent failures" and factory/packages/005_SERVICE_LIFECYCLE.md.

Responsibilities:
    - Provide a general lifecycle error base, and a more specific
      subtype for illegal state transitions, so callers can catch
      either the broad or the precise failure mode.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do not
      log, retry, or recover.

Dependencies:
    None.
"""


class LifecycleError(Exception):
    """Base exception for the lifecycle subsystem. Raised directly for
    failures that are not specifically an illegal state transition,
    such as looking up the status of a service the Lifecycle Manager
    has no entry for, or passing an invalid service name."""


class InvalidStateTransitionError(LifecycleError):
    """Raised when an operation would move a service from its current
    LifecycleState to a state that is not a legal next state (see
    argus.lifecycle.lifecycle for the valid transition graph)."""
