"""
Public interface contract for the ArgusOS Planning Session.

Purpose:
    Define IPlanningSessionBuilder, the contract other modules depend
    on, per factory/packages/023_PLANNING_SESSION.md, as amended by
    factory/packages/030_PLAN_TASK_INTEGRATION.md's own explicit "Add
    fluent methods: with_task(task), with_tasks(tasks), clear_tasks()"
    instruction.

Architectural Note - This Is Not An IService:
    Directly reuses argus.context.interfaces.ICognitiveContextBuilder's
    (Package 022) own resolution for the identical question: "This is
    not an IService" - settled by explicit instruction, not by
    applying ADR-0002's criterion. `IPlanningSessionBuilder` therefore
    extends plain `ABC`, matching both `ICognitiveContextBuilder`
    (022) and, further back, `IConnector`'s (017) original precedent
    for "a contract that is plain behavior, not a lifecycle-managed
    service." Consequently: `PlanningSessionBuilder` is never
    constructed in argus/bootstrap.py, never passed to
    Container.register(), never given a slot in the Lifecycle
    Manager's REGISTERED-state roster, and `PlanningSession`/
    `PlanningSessionBuilder` do not appear in CORE_SERVICE_NAMES
    (tests/test_bootstrap.py, argus/tests/test_bootstrap.py) at all -
    neither file was modified by this package. Every caller that
    wants a PlanningSession simply constructs
    `PlanningSessionBuilder()` directly, the same way any caller
    constructs a plain value object like `Entity` or `ReasoningQuery`
    - there is no service to look up. This is the second consecutive
    package (after 022) for which "is this an IService" was answered
    before implementation began, rather than left as this Engineer's
    own judgment call or an explicit adoption instruction to follow.

Architectural Note - No Events, No Lifecycle Gating Question:
    Because PlanningSessionBuilder is not an IService, the "which
    methods should be gated on RUNNING" question that every
    IService-adopting interface in this codebase documents simply
    does not arise here - there is no RUNNING state to gate against.
    Likewise, this package publishes no events: "No EventTypes."
    Every `with_*` method and build() below either mutates this
    builder's own private, in-process accumulator state or constructs
    a plain value object - neither is the kind of externally-visible
    occurrence this codebase's EventType convention exists to
    announce, directly mirroring
    argus.context.interfaces.ICognitiveContextBuilder's (022) own
    identical reasoning.

Responsibilities:
    - IPlanningSessionBuilder: with_context / with_goal /
      with_constraint / with_task / with_tasks / clear_tasks /
      with_metadata / build.

Non-Responsibilities:
    - This module implements no behavior; see
      argus.planning.builder.PlanningSessionBuilder.
    - IPlanningSessionBuilder does not perform planning, validate
      goals, optimize plans, or execute workflows - see this
      package's Objective and Constraints.

Dependencies:
    argus.context.context (CognitiveContext),
    argus.planning.constraint (PlanningConstraint),
    argus.planning.goal (PlanningGoal),
    argus.planning.session (PlanningSession),
    argus.task.task (Task) - Package 030.
"""

from abc import ABC, abstractmethod
from typing import Any, Sequence

from argus.context.context import CognitiveContext
from argus.planning.constraint import PlanningConstraint
from argus.planning.goal import PlanningGoal
from argus.planning.session import PlanningSession
from argus.task.task import Task


class IPlanningSessionBuilder(ABC):
    """
    Contract for a mutable, fluent PlanningSession builder. See this
    module's docstring for why IPlanningSessionBuilder does not
    inherit IService and why this package publishes no events.
    """

    @abstractmethod
    def with_context(self, cognitive_context: CognitiveContext) -> "IPlanningSessionBuilder":
        """Set this builder's cognitive_context. A later call
        overwrites an earlier one - the last call before build() wins.
        Raises InvalidPlanningSessionError if `cognitive_context` is
        not a CognitiveContext instance."""

    @abstractmethod
    def with_goal(self, goal: PlanningGoal) -> "IPlanningSessionBuilder":
        """Append one PlanningGoal. Accumulates across multiple calls.
        Raises InvalidPlanningSessionError if `goal` is not a
        PlanningGoal instance."""

    @abstractmethod
    def with_constraint(self, constraint: PlanningConstraint) -> "IPlanningSessionBuilder":
        """Append one PlanningConstraint. Accumulates across multiple
        calls. Raises InvalidPlanningSessionError if `constraint` is
        not a PlanningConstraint instance."""

    @abstractmethod
    def with_task(self, task: Task) -> "IPlanningSessionBuilder":
        """Append one Task. Accumulates across multiple calls. Raises
        InvalidPlanningSessionError if `task` is not a Task instance,
        or if its `task_id` matches a Task already accumulated -
        "no duplicates" (Package 030)."""

    @abstractmethod
    def with_tasks(self, tasks: Sequence[Task]) -> "IPlanningSessionBuilder":
        """Append every Task in `tasks`, in order, by calling
        with_task() once per item - not a second validation path.
        Raises InvalidPlanningSessionError if `tasks` is not a list or
        tuple, or if any item fails with_task()'s own validation."""

    @abstractmethod
    def clear_tasks(self) -> "IPlanningSessionBuilder":
        """Reset this builder's accumulated tasks back to empty.
        Does not affect any other accumulated field."""

    @abstractmethod
    def with_metadata(self, key: str, value: Any) -> "IPlanningSessionBuilder":
        """Set one arbitrary metadata key/value pair on the eventual
        PlanningSession.metadata.extra mapping. A later call with the
        same key overwrites an earlier one. Raises
        InvalidPlanningSessionError if `key` is not a non-empty
        string."""

    @abstractmethod
    def build(self) -> PlanningSession:
        """Construct and return a new, immutable PlanningSession
        snapshot from this builder's currently accumulated state.
        Performs no additional validation - every accumulated value
        was already validated by the `with_*` call that added it.
        Safe to call more than once; each call returns an independent
        PlanningSession."""
