"""
Public interface contracts for the ArgusOS Connector Framework.

Purpose:
    Define IConnector (the contract every connector implementation
    must satisfy) and IConnectorManager (the contract other modules
    depend on), per factory/packages/017_CONNECTOR_FRAMEWORK.md.

Architectural Note - Why IConnectorManager DOES Inherit IService:
    Unlike Capability Registry (013), Plugin Manager (014), and
    Planner (015) - deliberate non-adopters whose every public method
    is a plain registry operation - the Connector Framework's invoke()
    is squarely "real, distinct work": it is the one method that
    actually reaches out to an external system's connector
    implementation (calling connect() then invoke() on it), exactly
    analogous to IntentDispatcher.dispatch() (Package 012) and
    AgentRuntime.start_execution() (Package 016). Per ADR-0002's
    proposed criterion ("adopt IService only when start()/stop() would
    do real, distinct work"), invoke() is gated on the
    ConnectorManager's own lifecycle state being RUNNING.
    register_connector(), unregister_connector(), get_connector(),
    list_connectors(), enable_connector(), and disable_connector()
    remain ungated registry-style operations on individual Connectors,
    matching the precedent set by Scheduler's pause()/resume()
    (Package 008), AgentRuntime's pause_execution()/cancel_execution()
    (Package 016), and every metadata/reasoning registry's own lookup
    methods in this codebase - none of which are affected by the
    owning service's IService lifecycle. ConnectorManager is
    registered with the Lifecycle Manager as LifecycleState.REGISTERED
    only (never started) by bootstrap.py, exactly like every other
    IService adopter in this codebase - see
    design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md's newly
    appended Empirical Finding for this package, which records
    ConnectorManager as the seventh IService adopter and the sixth
    genuinely-gated one.

Responsibilities:
    - IConnector: connect / disconnect / invoke / health_check - the
      contract a concrete connector implementation (e.g.
      argus.connectors.manager.MockConnector) must satisfy.
    - IConnectorManager: register_connector / unregister_connector /
      get_connector / list_connectors / enable_connector /
      disable_connector / invoke, plus the inherited IService contract
      (initialize / start / stop / status).

Non-Responsibilities:
    - Neither interface implements any behavior; see
      argus.connectors.manager.ConnectorManager and
      argus.connectors.manager.MockConnector.
    - IConnectorManager does not execute Plans, create Plans, manage
      Plugins, or dispatch Intents - see argus.runtime.runtime.
      AgentRuntime, argus.planner.planner.Planner,
      argus.plugins.manager.PluginManager, and
      argus.dispatcher.dispatcher.IntentDispatcher for those
      responsibilities.

Dependencies:
    argus.connectors.connector (Connector), argus.lifecycle.interfaces
    (IService).
"""

from abc import ABC, abstractmethod
from typing import Any, Mapping, Optional, Sequence

from argus.connectors.connector import Connector
from argus.lifecycle.interfaces import IService


class IConnector(ABC):
    """
    Contract every connector implementation must satisfy.

    Purpose:
        Isolate external-system communication behind one common shape,
        so that ConnectorManager (and, transitively, anything above
        it) never needs to know whether a given connector's operations
        are backed by a mock (the only kind Version 1 ships) or, in a
        future package, a real external system.

    Note:
        An IConnector implementation is plain behavior - it carries no
        identity or metadata of its own; that is the separate,
        immutable Connector value object's responsibility (see
        argus/connectors/connector.py). ConnectorManager holds both,
        keyed by the same connector id, and never conflates them.
    """

    @abstractmethod
    def connect(self) -> None:
        """Establish this connector's connection. Must be safe to call
        when already connected (idempotent)."""

    @abstractmethod
    def disconnect(self) -> None:
        """Tear down this connector's connection. Must be safe to call
        when already disconnected (idempotent)."""

    @abstractmethod
    def invoke(
        self, operation: str, *, payload: Optional[Mapping[str, Any]] = None
    ) -> Mapping[str, Any]:
        """Perform `operation` against this connector, with an
        optional payload, returning a result mapping."""

    @abstractmethod
    def health_check(self) -> bool:
        """Report whether this connector is currently healthy /
        connected."""


class IConnectorManager(IService):
    """
    Contract for the Connector Framework's registry-and-invocation
    service. See this module's docstring for why IConnectorManager
    inherits IService and exactly which of its methods are gated.
    """

    @abstractmethod
    def register_connector(self, connector: Connector, implementation: IConnector) -> None:
        """Register a new Connector, together with the IConnector
        implementation that backs it. Raises DuplicateConnectorError
        if `connector.id` is already registered."""

    @abstractmethod
    def unregister_connector(self, connector_id: str) -> None:
        """Remove a previously registered connector. Raises
        ConnectorNotFoundError if `connector_id` is unknown."""

    @abstractmethod
    def get_connector(self, connector_id: str) -> Connector:
        """Return the Connector registered under `connector_id`.
        Raises ConnectorNotFoundError if unknown."""

    @abstractmethod
    def list_connectors(self) -> Sequence[Connector]:
        """Return every currently registered Connector."""

    @abstractmethod
    def enable_connector(self, connector_id: str) -> Connector:
        """Set `connector_id`'s Connector.enabled to True and return
        the updated Connector. Raises ConnectorNotFoundError if
        unknown."""

    @abstractmethod
    def disable_connector(self, connector_id: str) -> Connector:
        """Set `connector_id`'s Connector.enabled to False and return
        the updated Connector. Raises ConnectorNotFoundError if
        unknown."""

    @abstractmethod
    def invoke(
        self,
        connector_id: str,
        operation: str,
        *,
        payload: Optional[Mapping[str, Any]] = None,
    ) -> Mapping[str, Any]:
        """Invoke `operation` on the connector registered under
        `connector_id`, returning its result. Raises
        ConnectorNotFoundError if unknown, ConnectorDisabledError if
        the connector is disabled, InvalidConnectorStateError if the
        ConnectorManager itself is not RUNNING, and
        ConnectorInvocationError if the underlying connector
        implementation's connect() or invoke() call raises."""
