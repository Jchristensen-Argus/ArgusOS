"""
Interfaces for the ArgusOS Execution Engine package.

Purpose:
    Define IExecutionResultBuilder (the contract for a mutable,
    fluent ExecutionResult builder) and IExecutionEngine (the
    contract for the Execution Engine's own lifecycle service), per
    factory/packages/032_EXECUTION_ENGINE.md.

Architectural Note - IExecutionResultBuilder Does Not Inherit
IService:
    Exactly mirroring ICognitiveContextBuilder (022),
    IPlanningSessionBuilder (023), ITraceBuilder (028), ITaskBuilder
    (029), and IRelationshipBuilder (031), none of which inherit
    IService either - a builder has no meaningful start/stop
    lifecycle of its own; it is a short-lived, per-use accumulator.

Architectural Note - IExecutionEngine DOES Inherit IService, But
execute() Is Not Gated:
    "Register: ExecutionEngine. One new core service" is read the
    same way "Register: ResponseEngine" (027) was - "core service" is
    this codebase's own established shorthand for "adopts IService"
    (see argus/response/interfaces.py's own identical Architectural
    Note). Applying ADR-0002's criterion to execute() independently,
    however, would not have suggested adoption on its own: execute()
    is a synchronous, in-memory transformation of a Plan the caller
    already supplies - no external call, no dispatch to another live
    service, and no phase distinction it could plausibly be gated on,
    since ExecutionEngine's own constructor takes no dependency at
    all (see engine.py's own module docstring). This is
    architecturally the identical shape to ResponseEngine (027) -
    "no live collaborator to gate access to in the first place" - and
    makes IExecutionEngine the **sixth** zero-gated IService adopter
    in this codebase (after IntentRouter, KnowledgeGraph,
    ReasoningEngine, DecisionEngine, and ResponseEngine) and the
    **fifth** case where an explicit instruction to adopt IService
    diverges from what ADR-0002's own criterion would independently
    conclude (after Packages 018, 020, 021, and 027) - see
    design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md's newly
    appended Empirical Finding for this package. `ExecutionEngine` is
    also only the **second** core service in this codebase's own
    history - after `ResponseEngine` (027) - with a fully empty
    constructor, for the identical reason: its own sole "dependency,"
    the `Plan` it processes, is a per-call argument to execute(),
    never a constructor-injected collaborator. (Package 033 Amendment
    - see below: this "empty constructor" fact is historical as of
    Package 032 and no longer holds after Package 033's own
    constructor change; the zero-gated-adopter/divergent-case counts
    above remain accurate and unchanged, since gating behavior itself
    did not change.)

Architectural Note - Package 033 Amendment - A Constructor Dependency
Arrives, But Nothing Is Gated On It:
    Per Package 033's own explicit Integration instruction,
    `ExecutionEngine.__init__()` now accepts `capability_registry:
    ICapabilityRegistry` - "ExecutionEngine receives a reference to
    CapabilityRegistry but does not use it yet. The dependency exists
    only to establish future wiring... No behavior changes." This ends
    `ExecutionEngine`'s own brief run (027-032) as this codebase's
    second fully-empty-constructor core service - `ResponseEngine`
    (027) remains the sole surviving example - but does NOT change
    `execute()`'s own gating status: `execute()` still never checks
    `self._capability_registry`, still never checks lifecycle state,
    and is still callable in `CREATED`, `RUNNING`, or `STOPPED` alike.
    `IExecutionEngine` remains the sixth zero-gated IService adopter
    and the fifth divergent ADR-0002 case, both facts established at
    Package 032 and unchanged by this one - a constructor gaining a
    stored-but-unused dependency is not the same thing as a method
    gaining a gate, and ADR-0002's own criterion is about the latter.

Architectural Note - Package 034 Amendment - The Dependency Is Now
Used, But Still Nothing Is Gated:
    Package 034's own explicit Integration instruction replaces
    `ExecutionEngine.__init__()`'s own `capability_registry` parameter
    with `capability_executor: ICapabilityExecutor` - "ExecutionEngine
    now owns: CapabilityExecutor" - and, unlike Package 033's own
    change, this dependency is genuinely called: `execute()` now sends
    every Task to `capability_executor.resolve(task)` before placing
    it into `completed_tasks` (see engine.py's own module docstring).
    As of Package 035, that call site itself changes shape without
    changing this conclusion - `execute()` now wraps each Task in a
    locally-built CapabilityContext before calling
    `capability_executor.resolve(context)` (a breaking signature
    change on `resolve()` itself - see
    argus/capability_executor/interfaces.py's own "Package 035
    Amendment" note) - but `resolve()` remains exactly as zero-gated
    as before, so this note's own conclusion is unchanged.
    This still does not change `execute()`'s own gating status:
    `resolve()` is itself a zero-gated ICapabilityExecutor method (see
    argus/capability_executor/interfaces.py's own Architectural Note),
    so calling it introduces no phase distinction `execute()` could
    plausibly be gated on that did not already exist. `execute()`
    remains callable in `CREATED`, `RUNNING`, or `STOPPED` alike, and
    `IExecutionEngine` remains the sixth zero-gated IService adopter
    and the fifth divergent ADR-0002 case, both facts established at
    Package 032 and still unchanged by this package - only the
    *dependency being used* changed, not whether a gate exists to use
    it through.

Responsibilities:
    - IExecutionResultBuilder: the contract implemented by
      ExecutionResultBuilder.
    - IExecutionEngine: execute, plus the inherited IService contract
      (initialize / start / stop / status).

Non-Responsibilities:
    - This module defines no concrete behavior - see builder.py and
      engine.py.

Dependencies:
    argus.task.task (Task), argus.execution_engine.result
    (ExecutionResult), argus.execution_engine.status
    (ExecutionStatus), argus.planner.plan (Plan),
    argus.lifecycle.interfaces (IService).
"""

from abc import ABC, abstractmethod
from typing import Any, Sequence

from argus.execution_engine.result import ExecutionResult
from argus.execution_engine.status import ExecutionStatus
from argus.lifecycle.interfaces import IService
from argus.planner.plan import Plan
from argus.task.task import Task


class IExecutionResultBuilder(ABC):
    """
    Contract for a mutable, fluent ExecutionResult builder. See this
    module's docstring for why IExecutionResultBuilder does not
    inherit IService.
    """

    @abstractmethod
    def with_plan(self, plan: Plan) -> "IExecutionResultBuilder":
        """Set this builder's plan. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidExecutionResultError if `plan` is not a Plan
        instance."""

    @abstractmethod
    def with_completed_task(self, task: Task) -> "IExecutionResultBuilder":
        """Validate and append one Task to this builder's completed
        tasks, in call order. Accumulates across multiple calls.
        Raises InvalidExecutionResultError if `task` is not a Task
        instance."""

    @abstractmethod
    def with_completed_tasks(self, tasks: Sequence[Task]) -> "IExecutionResultBuilder":
        """Validate and append each item of `tasks` to this builder's
        completed tasks, in order, by delegating to
        with_completed_task() once per item. Raises
        InvalidExecutionResultError if `tasks` is not a list or
        tuple, or if any item is not a Task instance."""

    @abstractmethod
    def clear_completed_tasks(self) -> "IExecutionResultBuilder":
        """Reset this builder's accumulated completed tasks to
        empty."""

    @abstractmethod
    def with_failed_task(self, task: Task) -> "IExecutionResultBuilder":
        """Validate and append one Task to this builder's failed
        tasks, in call order. Accumulates across multiple calls.
        Raises InvalidExecutionResultError if `task` is not a Task
        instance."""

    @abstractmethod
    def with_failed_tasks(self, tasks: Sequence[Task]) -> "IExecutionResultBuilder":
        """Validate and append each item of `tasks` to this builder's
        failed tasks, in order, by delegating to with_failed_task()
        once per item. Raises InvalidExecutionResultError if `tasks`
        is not a list or tuple, or if any item is not a Task
        instance."""

    @abstractmethod
    def clear_failed_tasks(self) -> "IExecutionResultBuilder":
        """Reset this builder's accumulated failed tasks to empty."""

    @abstractmethod
    def with_status(self, status: ExecutionStatus) -> "IExecutionResultBuilder":
        """Set this builder's status. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidExecutionResultError if `status` is not an
        ExecutionStatus instance."""

    @abstractmethod
    def with_metadata(self, key: str, value: Any) -> "IExecutionResultBuilder":
        """Set one arbitrary metadata key/value pair on the eventual
        ExecutionMetadata.extra mapping. Accumulates across multiple
        calls; the same key overwrites - last call wins. Raises
        InvalidExecutionResultError if `key` is not a non-empty
        string."""

    @abstractmethod
    def build(self) -> ExecutionResult:
        """Construct and return a fresh, immutable ExecutionResult
        snapshot from this builder's current accumulated state."""


class IExecutionEngine(IService):
    """
    Contract for the Execution Engine's own lifecycle service. See
    this module's docstring for why IExecutionEngine inherits
    IService and why execute() is never gated.
    """

    @abstractmethod
    def execute(self, plan: Plan) -> ExecutionResult:
        """Accept and validate a `plan` reference, iterate through its
        ordered `plan.tasks` in order, and produce an immutable
        ExecutionResult. For Package 032, every Task is considered
        successfully processed - each is placed into the returned
        ExecutionResult's own `completed_tasks`, `failed_tasks` is
        always empty, and `status` is always ExecutionStatus.COMPLETED.
        Never invokes tools, calls APIs, or invokes AI - "It simply
        establishes the execution lifecycle." Never modifies `plan` or
        any Task it holds - both are already immutable value objects.
        Raises InvalidPlanReferenceError if `plan` is not a Plan
        instance."""
