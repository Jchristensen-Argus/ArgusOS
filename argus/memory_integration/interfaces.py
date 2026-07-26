"""
Public interface contract for the ArgusOS Memory Integration bridge.

Purpose:
    Define IMemoryIntegration, the contract other modules depend on,
    per factory/packages/019_MEMORY_INTEGRATION.md.

Architectural Note - IMemoryIntegration Inherits IService, With
Genuinely Gated Methods:
    Like Package 018's Knowledge Graph, this package's work order
    explicitly instructs "Create: IMemoryIntegration - Extend
    IService" - adoption itself is not a judgment call. Unlike
    Package 018, however, applying ADR-0002's criterion to this
    package's actual methods independently *would* have suggested
    adoption on its own: synchronize_memory(), synchronize_all(), and
    remove_memory() each perform genuine, effectful cross-system
    coordination - reading from IMemoryService and writing to
    IKnowledgeGraph in the same call - architecturally much closer to
    AgentRuntime.start_execution() (Package 016) and
    ConnectorManager.invoke() (Package 017) than to KnowledgeGraph's
    own purely in-memory, single-system operations (Package 018).
    These three methods are therefore genuinely gated on the
    service's own lifecycle state being RUNNING, raising
    InvalidMemoryIntegrationStateError otherwise. synchronization_status()
    and reset() remain ungated: both are pure, single-system
    operations over MemoryIntegration's own internal bookkeeping only
    (see argus/memory_integration/integration.py's module docstring,
    "It owns no data itself"), unaffected by whether the service has
    been started - matching Scheduler's pause()/resume() (Package
    008) and every other ungated registry-style operation in this
    codebase. This makes MemoryIntegration the case where an explicit
    adoption instruction and ADR-0002's own independently-applied
    criterion agree, in contrast with Package 018's Knowledge Graph,
    where they diverged - see
    design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md's newly
    appended Empirical Finding for this package. MemoryIntegration is
    registered with the Lifecycle Manager as LifecycleState.REGISTERED
    only (never started) by bootstrap.py, exactly like every other
    core service.

Architectural Note - `status()` Naming Collision, Resolved by
Renaming the Domain Method:
    This package's own work order lists `status()` as one of
    MemoryIntegration's five Responsibilities - but `IService.status()`
    is already a fixed abstract method returning `LifecycleState`,
    used identically (and exclusively for lifecycle reporting) by
    every other IService adopter in this codebase (Scheduler,
    IntentRouter, WorkflowEngine, ConversationManager,
    IntentDispatcher, AgentRuntime, ConnectorManager, KnowledgeGraph).
    A method cannot be named `status()` and simultaneously satisfy two
    incompatible contracts (LifecycleState vs. a synchronization-status
    snapshot) - silently overriding IService's own `status()` with a
    different return type would break Liskov substitution for any
    caller treating MemoryIntegration polymorphically as an IService.
    Given "Extend IService" is itself an explicit, non-negotiable
    instruction, and every other IService adopter in this codebase
    reserves `status()` exclusively for lifecycle reporting, this
    package's own domain-specific status method is named
    `synchronization_status()` instead - a deliberate, documented
    deviation from the work order's literal method name, required by
    an unavoidable naming collision between two of the same work
    order's own instructions.

Responsibilities:
    - IMemoryIntegration: synchronize_memory / remove_memory /
      synchronize_all / synchronization_status / reset, plus the
      inherited IService contract (initialize / start / stop /
      status).

Non-Responsibilities:
    - This module implements no behavior; see
      argus.memory_integration.integration.MemoryIntegration.
    - IMemoryIntegration does not store memory, modify Planner
      behavior, perform graph reasoning, execute Plans, or
      communicate externally - see this package's Objective and
      Constraints.

Dependencies:
    argus.lifecycle.interfaces (IService).
"""

from abc import abstractmethod
from typing import Any, Mapping, Sequence

from argus.lifecycle.interfaces import IService


class IMemoryIntegration(IService):
    """
    Contract for the Memory Integration bridge. See this module's
    docstring for why IMemoryIntegration inherits IService and
    exactly which of its methods are gated.
    """

    @abstractmethod
    def synchronize_memory(self, key: str) -> str:
        """Translate the MemoryRecord for `key` into a graph Entity
        (creating it if this is the first synchronization for `key`,
        or reconciling it in place otherwise - see integration.py),
        then translate and apply its `related_keys` Relationships on a
        best-effort basis. Returns the synchronized Entity's id.
        Raises InvalidMemoryRecordError if `key` has no corresponding
        MemoryRecord, MemoryMappingError if the Entity itself could
        not be added to the Knowledge Graph, and
        InvalidMemoryIntegrationStateError if this service is not
        RUNNING."""

    @abstractmethod
    def remove_memory(self, key: str) -> None:
        """Remove the graph Entity corresponding to `key` (and, via
        IKnowledgeGraph's own cascading removal, every Relationship
        referencing it). Raises MemoryNotSynchronizedError if `key`
        has no corresponding synchronized Entity, and
        InvalidMemoryIntegrationStateError if this service is not
        RUNNING."""

    @abstractmethod
    def synchronize_all(self) -> Sequence[str]:
        """Call synchronize_memory() for every record currently in
        the Memory Service, on a best-effort basis - one record's
        failure does not abort the batch. Returns the keys that were
        synchronized successfully. Raises
        InvalidMemoryIntegrationStateError if this service is not
        RUNNING."""

    @abstractmethod
    def synchronization_status(self) -> Mapping[str, Any]:
        """Return a snapshot of this service's own synchronization
        bookkeeping: which keys are currently synchronized, and which
        keys most recently failed to synchronize. Ungated - reflects
        internal state only, touches neither the Memory Service nor
        the Knowledge Graph. Named `synchronization_status()`, not
        `status()`, to avoid colliding with IService's own
        lifecycle-reporting `status()` - see this module's own
        Architectural Note."""

    @abstractmethod
    def reset(self) -> None:
        """Clear this service's own synchronization bookkeeping only.
        Does NOT remove anything from the Memory Service or the
        Knowledge Graph - "It owns no data itself." Ungated."""
