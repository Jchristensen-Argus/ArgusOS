"""
Public interface contract for the ArgusOS Decision Engine.

Purpose:
    Define IDecisionEngine, the contract other modules depend on, per
    factory/packages/021_DECISION_ENGINE.md.

Architectural Note - IDecisionEngine Inherits IService, But No
Method Is Gated:
    Like Package 018's Knowledge Graph and Package 020's Reasoning
    Engine, this package's work order explicitly instructs "Create:
    IDecisionEngine - Extending IService" - adoption itself is not a
    judgment call here. Applying ADR-0002's criterion to this
    package's actual methods independently, however, would not have
    suggested adoption: evaluate()/evaluate_all() call only
    caller-supplied, in-process Python predicates against
    caller-supplied ReasoningResult objects, and
    register_rule()/remove_rule()/list_rules()/decision_summary() are
    synchronous, in-memory registry operations over this engine's own
    rule table - no external call, no dispatch, no write to another
    system, and no phase distinction any of them could plausibly be
    gated on. "Its responsibility is limited to deterministic decision
    evaluation" - architecturally much closer to KnowledgeGraph
    (Package 018), ReasoningEngine (Package 020), and IntentRouter
    (Package 009) - all three zero-gated IService adopters - than to
    MemoryIntegration (Package 019), AgentRuntime (Package 016), or
    ConnectorManager (Package 017), whose genuinely gated methods each
    perform effectful, stateful cross-system coordination or external
    I/O that calling a local predicate function does not. Per the
    explicit instruction, `IDecisionEngine` DOES inherit `IService`
    and `DecisionEngine` implements the full
    initialize()/start()/stop()/status() lifecycle boilerplate - but
    none of the Decision Engine's own methods are gated on the
    RUNNING state, exactly mirroring KnowledgeGraph's (Package 018)
    and ReasoningEngine's (Package 020) identical shape. This makes
    DecisionEngine the fourth such case in this codebase, and the
    third consecutive package (018, 020, 021 - interrupted only by
    Package 019's convergent case) where an explicit Founder
    instruction to adopt IService does not align with what ADR-0002's
    own criterion would independently conclude - see
    design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md's newly
    appended Empirical Finding for this package. DecisionEngine is
    registered with the Lifecycle Manager as
    LifecycleState.REGISTERED only (never started) by bootstrap.py,
    exactly like every other core service - gated or not.

Architectural Note - The Injected IReasoningEngine Is Not Called in
Version 1:
    Unlike Package 020's Reasoning Engine (which genuinely calls its
    own injected IMemoryIntegration.synchronization_status() to
    enrich every result's metadata), DecisionEngine holds an injected
    IReasoningEngine - per this package's own explicit Bootstrap
    "Decision Engine depends on: Reasoning Engine" instruction - but
    does not call any of its methods in Version 1. Two things make
    this package's situation genuinely different from Package 020's,
    not merely a stylistic choice: first, this package's own
    Objective describes evaluate()/evaluate_all() operating on
    ReasoningResult objects the *caller* already supplies ("evaluates
    one or more ReasoningResult objects"), never on a live
    IReasoningEngine reference the Decision Engine would query itself
    - unlike Package 020's own Objective, which explicitly stated the
    Reasoning Engine itself "consumes information from... Memory
    Integration." Second, IReasoningEngine has no equivalent to
    IMemoryIntegration's zero-argument, whole-system
    synchronization_status() snapshot - every one of its six public
    methods requires a specific, meaningful query parameter
    (entity_id, relationship_type, and so on) that DecisionEngine has
    no principled, non-arbitrary way to supply blindly on every
    evaluate() call. Manufacturing a call (for example, to the
    inherited, always-CREATED status()) purely to claim "genuine use"
    would have been decorative, not functional. The dependency is
    still genuinely wired (constructor-injected, per the explicit
    Bootstrap instruction) so that a future package can extend
    DecisionEngine to query the Reasoning Engine directly once a
    concrete requirement to do so exists - a third distinct shape
    from this codebase's two prior precedents: Package 018's Planner/
    Knowledge Graph relationship (not wired into the constructor at
    all) and Package 020's Reasoning Engine/Memory Integration
    relationship (wired and genuinely called every time).

Responsibilities:
    - IDecisionEngine: evaluate / evaluate_all / register_rule /
      remove_rule / list_rules / decision_summary, plus the inherited
      IService contract (initialize / start / stop / status).

Non-Responsibilities:
    - This module implements no behavior; see
      argus.decision.engine.DecisionEngine.
    - IDecisionEngine does not modify memory, modify the graph,
      invoke planners, execute workflows, invoke connectors, or call
      LLMs - see this package's Objective and Constraints.

Dependencies:
    argus.decision.decision (Decision), argus.decision.rule
    (DecisionRule), argus.reasoning.result (ReasoningResult),
    argus.lifecycle.interfaces (IService).
"""

from abc import abstractmethod
from typing import Any, Mapping, Sequence

from argus.decision.decision import Decision
from argus.decision.rule import DecisionRule
from argus.lifecycle.interfaces import IService
from argus.reasoning.result import ReasoningResult


class IDecisionEngine(IService):
    """
    Contract for the Decision Engine's rule-evaluation service. See
    this module's docstring for why IDecisionEngine inherits IService
    despite none of its own methods being lifecycle-gated, and for why
    its injected IReasoningEngine dependency is not called in Version
    1.
    """

    @abstractmethod
    def evaluate(self, reasoning_result: ReasoningResult, *, decision_type: str) -> Decision:
        """Evaluate a single ReasoningResult against every registered
        DecisionRule, in priority order, and return a structured
        Decision. Equivalent to
        `evaluate_all((reasoning_result,), decision_type=decision_type)`
        - see evaluate_all()'s own docstring for the full evaluation
        semantics. Raises InvalidDecisionInputError for a malformed
        `reasoning_result` or `decision_type`, and RuleEvaluationError
        if a registered rule's own predicate raises."""

    @abstractmethod
    def evaluate_all(
        self, reasoning_results: Sequence[ReasoningResult], *, decision_type: str
    ) -> Decision:
        """Evaluate one or more ReasoningResult objects against every
        registered DecisionRule, in priority order (see
        list_rules()'s own docstring for the exact ordering rule).
        Every rule is evaluated - there is no "stop at first match."
        Returns a single Decision whose `matched_rules` holds every
        rule whose predicate returned True, and whose `metadata`
        holds a full per-rule matched/not-matched trace (see
        engine.py's own module docstring). Raises
        InvalidDecisionInputError if `reasoning_results` is empty or
        contains a non-ReasoningResult item, or `decision_type` is
        not a non-empty string. Raises RuleEvaluationError - aborting
        the whole call, with no Decision returned - if any registered
        rule's own predicate raises."""

    @abstractmethod
    def register_rule(self, rule: DecisionRule) -> None:
        """Register a new DecisionRule. Raises
        InvalidDecisionRuleError if `rule` is not a DecisionRule
        instance, or has an empty id/name, a non-integer priority, or
        a non-callable predicate. Raises DuplicateRuleError if
        `rule.id` is already registered."""

    @abstractmethod
    def remove_rule(self, rule_id: str) -> None:
        """Remove a previously registered DecisionRule. Raises
        RuleNotFoundError if `rule_id` is unknown."""

    @abstractmethod
    def list_rules(self) -> Sequence[DecisionRule]:
        """Return every currently registered DecisionRule, sorted by
        priority ascending (lower priority values first), with ties
        broken by registration order - the same deterministic order
        evaluate()/evaluate_all() themselves use."""

    @abstractmethod
    def decision_summary(self) -> Mapping[str, Any]:
        """Return a structural, descriptive snapshot of this engine's
        own currently registered rule set (rule count and each rule's
        id/name/priority, in evaluation order) - not a history of past
        Decisions, which this package does not retain (see this
        package's own "implement persistence" Constraint). For the
        outcome of a specific evaluation, see that call's own returned
        Decision.metadata instead."""


# ---------------------------------------------------------------------------
# argus.decision.decision_record - IDecisionRecordBuilder
# ---------------------------------------------------------------------------
#
# Appended per factory/packages/039_DECISION_FRAMEWORK.md. Everything above
# this point is Package 021's own Decision Engine contract (IDecisionEngine)
# and is unmodified. IDecisionRecordBuilder is a wholly independent contract
# for the new DecisionRecord domain object introduced by Package 039 - see
# argus/decision/decision_record.py's own module docstring for why this
# package's model is named DecisionRecord rather than Decision, to avoid
# colliding with IDecisionEngine's own pre-existing Decision concept above.
# IDecisionRecordBuilder does not inherit IService, exactly mirroring
# IGoalBuilder (038) / IProjectBuilder (036) / IWorkspaceBuilder (037) - a
# builder has no meaningful start/stop lifecycle of its own.

from abc import ABC  # noqa: E402
from argus.decision.decision_record import DecisionRecord  # noqa: E402
from argus.decision.priority import DecisionRecordPriority  # noqa: E402
from argus.decision.status import DecisionRecordStatus  # noqa: E402


class IDecisionRecordBuilder(ABC):
    """
    Contract for a mutable, fluent DecisionRecord builder. See this
    module's own DecisionRecord section header for why
    IDecisionRecordBuilder does not inherit IService, and
    decision_record.py's own module docstring for why this concept is
    named DecisionRecord rather than Decision.
    """

    @abstractmethod
    def with_title(self, title: str) -> "IDecisionRecordBuilder":
        """Set this builder's title. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidDecisionRecordError if `title` is not a non-empty
        string."""

    @abstractmethod
    def with_question(self, question: str) -> "IDecisionRecordBuilder":
        """Set this builder's question. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidDecisionRecordError if `question` is not a non-empty
        string."""

    @abstractmethod
    def with_status(self, status: DecisionRecordStatus) -> "IDecisionRecordBuilder":
        """Set this builder's status. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidDecisionRecordError if `status` is not a
        DecisionRecordStatus instance."""

    @abstractmethod
    def with_priority(self, priority: DecisionRecordPriority) -> "IDecisionRecordBuilder":
        """Set this builder's priority. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidDecisionRecordError if `priority` is not a
        DecisionRecordPriority instance."""

    @abstractmethod
    def with_metadata(self, key: str, value: Any) -> "IDecisionRecordBuilder":
        """Set one arbitrary metadata key/value pair on the eventual
        DecisionRecordMetadata.extra mapping. Accumulates across
        multiple calls; the same key overwrites - last call wins.
        Raises InvalidDecisionRecordError if `key` is not a
        non-empty string."""

    @abstractmethod
    def build(self) -> DecisionRecord:
        """Construct and return a fresh, immutable DecisionRecord
        snapshot from this builder's current accumulated state."""
