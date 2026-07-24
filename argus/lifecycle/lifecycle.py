"""
Lifecycle state machine for ArgusOS services.

Purpose:
    Define the closed set of runtime lifecycle states every ArgusOS
    service passes through, and provide an in-memory manager that
    tracks each named service's current state and enforces legal
    transitions between states, per
    factory/packages/005_SERVICE_LIFECYCLE.md.

Responsibilities:
    - Define LifecycleState, the only valid runtime states.
    - Track the current LifecycleState of every service known to the
      manager, keyed by service name.
    - Validate every requested transition against the fixed set of
      legal edges; reject illegal transitions explicitly.
    - Report the current state of a tracked service.

Non-Responsibilities:
    - This module does not hold or call real service instances. It
      tracks state for a service name only; wiring an actual IService
      implementation's initialize()/start()/stop() calls to these
      transitions is future work, not part of this package.
    - No persistence, no timers, no background workers, no automatic
      dependency resolution, no threads, no async.

Dependencies:
    argus.lifecycle.exceptions (LifecycleError, InvalidStateTransitionError).
"""

from enum import Enum, auto
from typing import Dict, FrozenSet, Optional

from argus.lifecycle.exceptions import InvalidStateTransitionError, LifecycleError


class LifecycleState(Enum):
    """The only valid runtime lifecycle states for an ArgusOS service."""

    CREATED = auto()
    REGISTERED = auto()
    INITIALIZING = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()
    FAILED = auto()


# States from which a service may transition to FAILED ("any active
# state"). CREATED is never itself stored (see LifecycleManager), and
# STOPPED/FAILED are terminal, so they are excluded.
_FAILABLE_STATES: FrozenSet[LifecycleState] = frozenset(
    {
        LifecycleState.REGISTERED,
        LifecycleState.INITIALIZING,
        LifecycleState.RUNNING,
        LifecycleState.STOPPING,
    }
)


class LifecycleManager:
    """
    In-memory tracker and validator for ArgusOS service lifecycle
    states.

    Purpose:
        Give every ArgusOS service the same initialization, startup,
        shutdown, and status model, per Package 005, independent of
        what the service actually does.

    Responsibilities:
        - register(name): CREATED -> REGISTERED, for a name not yet
          known to the manager.
        - initialize(name): REGISTERED -> INITIALIZING.
        - start(name): INITIALIZING -> RUNNING.
        - stop(name): RUNNING -> STOPPING -> STOPPED, in one call (see
          the Package 005 engineering notes: no separate method exists
          for the STOPPING -> STOPPED edge).
        - fail(name): any active state -> FAILED (see docstring below
          for why this method exists beyond the suggested API).
        - status(name): report the current LifecycleState.
        - Reject every illegal transition with InvalidStateTransitionError.

    Dependencies:
        None.
    """

    def __init__(self) -> None:
        self._states: Dict[str, LifecycleState] = {}

    def register(self, service_name: str) -> None:
        """
        Register a new service name, entering LifecycleState.REGISTERED.

        Parameters:
            service_name: The name to register. Must not be already
                known to this manager.

        Raises:
            LifecycleError: If service_name is empty.
            InvalidStateTransitionError: If service_name is already
                registered.
        """
        self._require_name(service_name)
        current = self._states.get(service_name)
        if current is not None:
            raise InvalidStateTransitionError(
                f"Cannot register {service_name!r}: already registered "
                f"(current state {current.name})."
            )
        self._states[service_name] = LifecycleState.REGISTERED

    def initialize(self, service_name: str) -> None:
        """
        Transition a registered service to LifecycleState.INITIALIZING.

        Raises:
            InvalidStateTransitionError: If service_name is not
                currently REGISTERED (including if it was never
                registered at all).
        """
        self._transition(
            service_name,
            required_current=LifecycleState.REGISTERED,
            target=LifecycleState.INITIALIZING,
        )

    def start(self, service_name: str) -> None:
        """
        Transition an initializing service to LifecycleState.RUNNING.

        Raises:
            InvalidStateTransitionError: If service_name is not
                currently INITIALIZING.
        """
        self._transition(
            service_name,
            required_current=LifecycleState.INITIALIZING,
            target=LifecycleState.RUNNING,
        )

    def stop(self, service_name: str) -> None:
        """
        Transition a running service to LifecycleState.STOPPED, by way
        of STOPPING.

        Raises:
            InvalidStateTransitionError: If service_name is not
                currently RUNNING.
        """
        self._transition(
            service_name,
            required_current=LifecycleState.RUNNING,
            target=LifecycleState.STOPPING,
        )
        # STOPPING -> STOPPED is always legal immediately after the
        # transition above; no separate public method exists for it,
        # per the Package 005 engineering notes.
        self._states[service_name] = LifecycleState.STOPPED

    def fail(self, service_name: str) -> None:
        """
        Transition a service to LifecycleState.FAILED from any active
        (non-terminal) state.

        This method is not one of the five names in Package 005's
        "Suggested public API", which the work order frames as a
        suggestion rather than an exhaustive list. FAILED is a
        required state ("Failure may transition any active state to
        FAILED") that none of register/initialize/start/stop can ever
        produce, so this method is the only way to make FAILED
        reachable. See the Package 005 engineering notes.

        Raises:
            InvalidStateTransitionError: If service_name has never
                been registered, or is already STOPPED or FAILED.
        """
        self._require_name(service_name)
        current = self._states.get(service_name)
        if current not in _FAILABLE_STATES:
            state_description = current.name if current else "an unregistered state"
            raise InvalidStateTransitionError(
                f"Cannot fail {service_name!r} from {state_description}."
            )
        self._states[service_name] = LifecycleState.FAILED

    def status(self, service_name: str) -> LifecycleState:
        """
        Report a service's current LifecycleState.

        Raises:
            LifecycleError: If service_name is empty or has never been
                registered.
        """
        self._require_name(service_name)
        current = self._states.get(service_name)
        if current is None:
            raise LifecycleError(f"No lifecycle entry for service {service_name!r}.")
        return current

    def _transition(
        self,
        service_name: str,
        required_current: LifecycleState,
        target: LifecycleState,
    ) -> None:
        self._require_name(service_name)
        current: Optional[LifecycleState] = self._states.get(service_name)
        if current != required_current:
            current_description = current.name if current else "unregistered"
            raise InvalidStateTransitionError(
                f"Cannot move {service_name!r} to {target.name}: current "
                f"state is {current_description}, expected "
                f"{required_current.name}."
            )
        self._states[service_name] = target

    @staticmethod
    def _require_name(service_name: str) -> None:
        if not service_name:
            raise LifecycleError("service_name must not be empty.")
