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
    never a constructor-injected collaborator.

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
