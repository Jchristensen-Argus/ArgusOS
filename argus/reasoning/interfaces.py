"""
Public interface contract for the ArgusOS Reasoning Engine.

Purpose:
    Define IReasoningEngine, the contract other modules depend on,
    per factory/packages/020_REASONING_ENGINE.md.

Architectural Note - IReasoningEngine Inherits IService, But No
Method Is Gated:
    Like Package 018's Knowledge Graph, this package's work order
    explicitly instructs "Create: IReasoningEngine - Extend IService"
    - adoption itself is not a judgment call here. Applying ADR-0002's
    criterion to this package's actual methods independently, however,
    would not have suggested adoption: query()/neighbors()/
    find_paths()/related_entities()/entity_summary()/
    relationship_summary() are all synchronous, read-only, in-memory
    operations over an already-injected IKnowledgeGraph (and, for
    metadata enrichment only, IMemoryIntegration.synchronization_status()
    - see engine.py's own Architectural Decision) - no external call,
    no dispatch, no write, and no phase distinction any of them could
    plausibly be gated on. "It does not make decisions. It does not
    execute plans. It performs deterministic reasoning only" -
    architecturally much closer to KnowledgeGraph (Package 018) and
    IntentRouter (Package 009) - both zero-gated IService adopters -
    than to MemoryIntegration (Package 019), AgentRuntime (Package
    016), or ConnectorManager (Package 017), whose genuinely gated
    methods each perform effectful, genuinely stateful cross-system
    coordination or external I/O that reading a graph does not. Per
    the explicit instruction, `IReasoningEngine` DOES inherit
    `IService` and `ReasoningEngine` implements the full
    initialize()/start()/stop()/status() lifecycle boilerplate - but
    none of the Reasoning Engine's own methods are gated on the
    RUNNING state, exactly mirroring KnowledgeGraph's (Package 018)
    and IntentRouter's (Package 009) identical shape. This makes
    ReasoningEngine the third such case in this codebase - see
    design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md's newly
    appended Empirical Finding for this package, which also contrasts
    this divergent case with Package 019's Memory Integration, where
    explicit instruction and the criterion's own independent
    conclusion agreed. ReasoningEngine is registered with the
    Lifecycle Manager as LifecycleState.REGISTERED only (never
    started) by bootstrap.py, exactly like every other core service -
    gated or not.

Responsibilities:
    - IReasoningEngine: query / neighbors / find_paths /
      related_entities / entity_summary / relationship_summary, plus
      the inherited IService contract (initialize / start / stop /
      status).

Non-Responsibilities:
    - This module implements no behavior; see
      argus.reasoning.engine.ReasoningEngine.
    - IReasoningEngine does not invoke LLMs, perform probabilistic
      reasoning, modify the Knowledge Graph, modify memory, execute
      actions, or communicate externally - see this package's
      Objective and Constraints.

Dependencies:
    argus.reasoning.query (ReasoningQuery),
    argus.reasoning.result (ReasoningResult),
    argus.lifecycle.interfaces (IService).
"""

from abc import abstractmethod
from typing import Optional

from argus.lifecycle.interfaces import IService
from argus.reasoning.query import ReasoningQuery
from argus.reasoning.result import ReasoningResult


class IReasoningEngine(IService):
    """
    Contract for the Reasoning Engine's read-only query service. See
    this module's docstring for why IReasoningEngine inherits
    IService despite none of its own methods being lifecycle-gated.
    """

    @abstractmethod
    def query(self, reasoning_query: ReasoningQuery) -> ReasoningResult:
        """Evaluate a ReasoningQuery against the Knowledge Graph and
        return a structured ReasoningResult. See
        argus/reasoning/query.py's module docstring for the exact
        branching rules. Raises InvalidReasoningQueryError for a
        malformed query, and ReasoningTargetNotFoundError if
        `reasoning_query.entity_id` is set but not registered."""

    @abstractmethod
    def neighbors(self, entity_id: str) -> ReasoningResult:
        """Return every Entity directly connected to `entity_id` by
        at least one Relationship, in either direction (matching
        IKnowledgeGraph.neighbors()' own single-hop, direction-
        agnostic semantics), together with the connecting
        Relationships themselves. Raises ReasoningTargetNotFoundError
        if `entity_id` is unknown."""

    @abstractmethod
    def find_paths(
        self, source_entity_id: str, target_entity_id: str, *, max_depth: int = 3
    ) -> ReasoningResult:
        """Deterministically enumerate every simple path (no repeated
        Entities) connecting `source_entity_id` to `target_entity_id`,
        treating each Relationship as traversable in either direction
        (matching neighbors()' own convention), whose length does not
        exceed `max_depth` hops. Returns an empty result if no such
        path exists - this is not an error. Raises
        InvalidReasoningQueryError if `max_depth` is not a positive
        integer, and ReasoningTargetNotFoundError if either endpoint
        is unknown."""

    @abstractmethod
    def related_entities(
        self, entity_id: str, *, relationship_type: Optional[str] = None
    ) -> ReasoningResult:
        """Like neighbors(), but optionally restricted to
        Relationships whose relationship_type equals
        `relationship_type` (unset means unrestricted, equivalent to
        neighbors()). Raises ReasoningTargetNotFoundError if
        `entity_id` is unknown."""

    @abstractmethod
    def entity_summary(self, entity_id: str) -> ReasoningResult:
        """Return a descriptive, single-Entity summary: the Entity
        itself, every Relationship touching it in either direction,
        and count-based metadata (outgoing/incoming/neighbor counts).
        Raises ReasoningTargetNotFoundError if `entity_id` is
        unknown."""

    @abstractmethod
    def relationship_summary(self, relationship_type: str) -> ReasoningResult:
        """Return a descriptive, graph-wide summary of every
        Relationship whose relationship_type equals
        `relationship_type`: the Relationships themselves, every
        distinct Entity that is one of their endpoints, and
        count-based metadata. Raises InvalidReasoningQueryError if
        `relationship_type` is not a non-empty string."""
