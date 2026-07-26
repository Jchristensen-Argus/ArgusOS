"""
ConnectorManager and MockConnector for the ArgusOS Connector
Framework.

Purpose:
    Implement IConnectorManager: an in-memory registry of Connector
    metadata paired with the live IConnector implementations that
    back them, exposing register/unregister/get/list/enable/disable
    plus a single gated invoke() entry point - per
    factory/packages/017_CONNECTOR_FRAMEWORK.md. The framework owns
    connectivity only: it never executes Plans, creates Plans, manages
    Plugins, dispatches Intents, or performs business logic.

    This module also ships MockConnector, the one concrete IConnector
    implementation Version 1 provides, per this package's explicit
    "No real integrations yet. Use mock connectors only" instruction.

Scope Note (Package Structure) - Why MockConnector Lives Here, Not in
`connector.py`:
    This package's explicit file list (`__init__.py, connector.py,
    manager.py, interfaces.py, exceptions.py`) has no separate file
    for a concrete connector implementation. Placing MockConnector in
    connector.py would force connector.py to import IConnector from
    interfaces.py, while interfaces.py already imports Connector from
    connector.py for typing IConnectorManager's methods - a circular
    import. manager.py already depends on both connector.py and
    interfaces.py and nothing in the package depends on manager.py, so
    placing MockConnector here keeps connector.py a pure,
    dependency-free leaf (matching the precedent set by
    argus.capability.capability, argus.plugins.plugin, argus.planner.
    plan, and argus.runtime.execution) while introducing no cycle.

Responsibilities:
    - ConnectorManager: the sole implementation of IConnectorManager.
    - MockConnector: a simple, fully in-memory IConnector
      implementation with no network, no I/O, and no external process
      of any kind - used both for this package's own bootstrap-time
      built-in connector and for testing.

Non-Responsibilities:
    - ConnectorManager never executes Plans, creates Plans, reorders
      PlanSteps, manages Plugins, or dispatches Intents - see
      argus.runtime.runtime.AgentRuntime, argus.planner.planner.
      Planner, argus.plugins.manager.PluginManager, and argus.
      dispatcher.dispatcher.IntentDispatcher for those
      responsibilities.
    - ConnectorManager.invoke() does not automatically call
      disconnect() after a successful invocation - see this class's
      own invoke() docstring, "Connection Handling," for the full
      rationale.

Dependencies:
    argus.connectors.connector (Connector), argus.connectors.
    exceptions, argus.connectors.interfaces (IConnector,
    IConnectorManager), argus.events (Event, EventType, IEventBus),
    argus.lifecycle.lifecycle (LifecycleState).
"""

import dataclasses
from typing import Any, Dict, Mapping, Optional, Sequence

from argus.connectors.connector import Connector
from argus.connectors.exceptions import (
    ConnectorDisabledError,
    ConnectorError,
    ConnectorInvocationError,
    ConnectorNotFoundError,
    DuplicateConnectorError,
    InvalidConnectorError,
    InvalidConnectorStateError,
)
from argus.connectors.interfaces import IConnector, IConnectorManager
from argus.events.event import Event
from argus.events.event_types import EventType
from argus.events.interfaces import IEventBus
from argus.lifecycle.lifecycle import LifecycleState


class MockConnector(IConnector):
    """
    A simple, fully in-memory IConnector implementation - the one
    concrete connector Version 1 ships, per this package's "No real
    integrations yet. Use mock connectors only" instruction.

    Behavior:
        connect()/disconnect() toggle an internal `_connected` flag
        (both are idempotent - calling either while already in that
        state is a no-op). invoke() raises ConnectorInvocationError if
        called while not connected; otherwise it returns a small,
        fixed result mapping (configurable via `response`) merged with
        the requested `operation` and `payload`, so a caller can
        confirm exactly what was invoked. health_check() simply
        returns the current `_connected` flag.

    Note:
        This "raise if not connected" behavior is only reachable when
        an IConnector implementation is exercised directly (as
        tests/test_connector.py does) - ConnectorManager.invoke()
        always calls connect() immediately before invoke() (see
        ConnectorManager.invoke()'s docstring), so a MockConnector
        driven only through ConnectorManager never hits this path.
    """

    def __init__(self, *, response: Optional[Mapping[str, Any]] = None) -> None:
        self._connected = False
        self._response: Dict[str, Any] = dict(response) if response else {"ok": True}

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def invoke(
        self, operation: str, *, payload: Optional[Mapping[str, Any]] = None
    ) -> Mapping[str, Any]:
        if not self._connected:
            raise ConnectorInvocationError(
                "MockConnector is not connected; call connect() first."
            )
        result = dict(self._response)
        result["operation"] = operation
        result["payload"] = dict(payload) if payload else {}
        return result

    def health_check(self) -> bool:
        return self._connected


class ConnectorManager(IConnectorManager):
    """
    In-memory implementation of IConnectorManager.

    Purpose:
        Track registered Connector metadata alongside the live
        IConnector implementations that back them, and provide the
        single, gated invoke() entry point through which every
        external-system call in ArgusOS must pass. See the module
        docstring for the full design rationale.

    Dependencies:
        An IEventBus, injected by the caller (bootstrap.py).
    """

    def __init__(self, event_bus: IEventBus) -> None:
        self._event_bus = event_bus
        self._connectors: Dict[str, Connector] = {}
        self._implementations: Dict[str, IConnector] = {}
        self._state: LifecycleState = LifecycleState.CREATED

    # -- IService -----------------------------------------------------

    def initialize(self) -> None:
        if self._state != LifecycleState.CREATED:
            raise ConnectorError(
                f"Cannot initialize: ConnectorManager is {self._state.name}, expected CREATED."
            )
        self._state = LifecycleState.INITIALIZING

    def start(self) -> None:
        if self._state != LifecycleState.INITIALIZING:
            raise ConnectorError(
                f"Cannot start: ConnectorManager is {self._state.name}, expected INITIALIZING."
            )
        self._state = LifecycleState.RUNNING

    def stop(self) -> None:
        if self._state != LifecycleState.RUNNING:
            raise ConnectorError(
                f"Cannot stop: ConnectorManager is {self._state.name}, expected RUNNING."
            )
        self._state = LifecycleState.STOPPING
        self._state = LifecycleState.STOPPED

    def status(self) -> LifecycleState:
        return self._state

    # -- IConnectorManager: registry operations (ungated) ----------------

    def register_connector(self, connector: Connector, implementation: IConnector) -> None:
        if not isinstance(connector, Connector):
            raise InvalidConnectorError(
                f"register_connector() requires a Connector, got {connector!r}."
            )
        if not connector.id:
            raise InvalidConnectorError("Connector.id must be non-empty.")
        if not connector.name:
            raise InvalidConnectorError("Connector.name must be non-empty.")
        if not connector.version:
            raise InvalidConnectorError("Connector.version must be non-empty.")
        if implementation is None:
            raise InvalidConnectorError("register_connector() requires an implementation.")
        if connector.id in self._connectors:
            raise DuplicateConnectorError(f"Connector {connector.id!r} is already registered.")

        self._connectors[connector.id] = connector
        self._implementations[connector.id] = implementation
        self._publish(EventType.CONNECTOR_REGISTERED, {"connector_id": connector.id})

    def unregister_connector(self, connector_id: str) -> None:
        self._require_connector(connector_id)
        del self._connectors[connector_id]
        del self._implementations[connector_id]
        # No CONNECTOR_UNREGISTERED event exists: this package's own
        # Events section names exactly five event types, none of them
        # for unregister - matching PLAN_REMOVED's (Package 015)
        # precedent of not inventing an event beyond what was asked.

    def get_connector(self, connector_id: str) -> Connector:
        return self._require_connector(connector_id)

    def list_connectors(self) -> Sequence[Connector]:
        return tuple(self._connectors.values())

    def enable_connector(self, connector_id: str) -> Connector:
        connector = self._require_connector(connector_id)
        updated = dataclasses.replace(connector, enabled=True)
        self._connectors[connector_id] = updated
        self._publish(EventType.CONNECTOR_ENABLED, {"connector_id": connector_id})
        return updated

    def disable_connector(self, connector_id: str) -> Connector:
        connector = self._require_connector(connector_id)
        updated = dataclasses.replace(connector, enabled=False)
        self._connectors[connector_id] = updated
        self._publish(EventType.CONNECTOR_DISABLED, {"connector_id": connector_id})
        return updated

    # -- IConnectorManager: invoke (gated) -------------------------------

    def invoke(
        self,
        connector_id: str,
        operation: str,
        *,
        payload: Optional[Mapping[str, Any]] = None,
    ) -> Mapping[str, Any]:
        """
        Connection Handling:
            invoke() always calls the underlying implementation's
            connect() immediately before calling its invoke() -
            connect() is required to be idempotent (see IConnector's
            contract), so this is safe whether or not the connector
            was already connected. invoke() does NOT call disconnect()
            afterwards, leaving the connector connected for any
            subsequent invocation ("connect once, invoke many times").
            Version 1 has no automatic idle-teardown policy; a future
            package may add one once real (non-mock) integrations
            exist.
        """
        if self._state != LifecycleState.RUNNING:
            raise InvalidConnectorStateError(
                f"Cannot invoke: ConnectorManager is {self._state.name}, expected RUNNING."
            )
        connector = self._require_connector(connector_id)
        if not connector.enabled:
            raise ConnectorDisabledError(f"Connector {connector_id!r} is disabled.")
        if not isinstance(operation, str) or not operation:
            raise InvalidConnectorError("invoke() requires a non-empty operation string.")

        implementation = self._implementations[connector_id]
        try:
            implementation.connect()
            result = implementation.invoke(operation, payload=payload)
        except Exception as error:
            self._publish(
                EventType.CONNECTOR_FAILED,
                {"connector_id": connector_id, "operation": operation, "error": str(error)},
            )
            raise ConnectorInvocationError(
                f"Connector {connector_id!r} failed to invoke {operation!r}: {error}"
            ) from error

        self._publish(
            EventType.CONNECTOR_INVOKED,
            {"connector_id": connector_id, "operation": operation},
        )
        return result

    # -- internal helpers -------------------------------------------------

    def _require_connector(self, connector_id: str) -> Connector:
        if not isinstance(connector_id, str) or not connector_id:
            raise InvalidConnectorError("connector_id must be a non-empty string.")
        try:
            return self._connectors[connector_id]
        except KeyError:
            raise ConnectorNotFoundError(f"No connector registered under {connector_id!r}.")

    def _publish(self, event_type: EventType, payload: dict) -> None:
        self._event_bus.publish(
            Event(type=event_type, source="connector_manager", payload=payload)
        )
