"""
The PlanningSessionBuilder for the ArgusOS Planning Session.

Purpose:
    Provide a mutable, fluent way to accumulate a PlanningSession's
    fields one at a time before producing a single immutable
    PlanningSession snapshot, per
    factory/packages/023_PLANNING_SESSION.md. "Builder is mutable.
    PlanningSession is immutable. Each call to build() returns an
    independent immutable snapshot." Every `with_*` method validates
    its own input, then mutates this builder's internal accumulator
    state and returns `self`, so calls chain:
    `PlanningSessionBuilder().with_context(ctx).with_goal(g1).build()`.
    Directly mirrors argus.context.builder.ContextBuilder's (Package
    022) own shape, accumulation rules, and validation discipline -
    the same builder pattern applied one layer further into the
    cognitive pipeline.

Accumulate, Except For Context:
    with_goal(), with_constraint(), with_task(), and with_metadata()
    each accumulate - calling with_goal() three times with three
    different PlanningGoal objects produces a PlanningSession whose
    goals holds all three, in call order. with_context() is the one
    exception: cognitive_context is a single scalar field, not a
    collection, so calling it more than once simply overwrites the
    previous value - the last call before build() wins. This mirrors
    ContextBuilder.with_conversation()'s (022) identical
    "singular field is overwritten, collection field accumulates"
    distinction.

Package 030 Amendment - with_task() / with_tasks() / clear_tasks():
    Per factory/packages/030_PLAN_TASK_INTEGRATION.md's own explicit
    "Add fluent methods: with_task(task), with_tasks(tasks),
    clear_tasks()" instruction, this builder gained three new methods.
    with_task(task) validates and appends one Task (Package 029),
    accumulating like with_goal()/with_constraint(); it additionally
    rejects a Task whose task_id matches one already accumulated -
    "no duplicates" (Package 030's own explicit Plan requirement,
    enforced here on the PlanningSession side, and again by Planner on
    the Plan side - see argus.planner.planner's own module docstring).
    with_tasks(tasks) accepts any list/tuple of Task objects and calls
    with_task() once per item, in order - not a second, parallel
    validation path, the same "delegate to the one method that already
    validates" discipline this codebase's own plan_session() (Package
    024) already established for "no duplicate planning logic."
    clear_tasks() resets this builder's own accumulated tasks back to
    empty and returns self - the first "reset a collection" method any
    builder in this codebase has ever exposed; every prior builder
    (ContextBuilder, PlanningSessionBuilder's own pre-030 methods,
    TraceBuilder, TaskBuilder) only ever accumulates or overwrites, so
    clear_tasks() is a genuinely new capability, not a mirror of an
    existing method's shape.

with_metadata() Only Ever Populates `extra`:
    PlanningMetadata's `created_at`, `version`, and `correlation_id`
    fields are system-assigned at PlanningSession construction time
    (see metadata.py's own module docstring) - PlanningSessionBuilder
    exposes no way to override them. with_metadata(key, value) adds
    one key/value pair to the eventual PlanningMetadata.extra mapping;
    calling it multiple times with different keys accumulates, and
    calling it twice with the same key overwrites that key's value -
    the last call wins, the same last-call-wins rule with_context
    uses.

Validation Lives Here, Not On PlanningSession/PlanningGoal/
PlanningConstraint/Task:
    See session.py's own module docstring - PlanningSession performs
    no validation of its own; every `with_*` method below validates
    its argument before accumulating it, raising
    InvalidPlanningSessionError for malformed input - including
    with_task()'s own duplicate-`task_id` check, since Task itself (per
    argus.task.task's own module docstring) also performs no
    validation of its own. build() itself performs no additional
    validation - by the time build() runs, every accumulated value has
    already been validated at the point it was added.

Independent Snapshots:
    build() constructs a fresh PlanningSession (and a fresh
    PlanningMetadata) from this builder's current accumulated state
    every time it is called. Continuing to call `with_*` methods on
    the same builder after calling build() - or calling build() more
    than once - never mutates a PlanningSession already returned by an
    earlier build() call, since PlanningSession's own __post_init__
    copies every mutable sequence it is given (see session.py).

Responsibilities:
    - PlanningSessionBuilder: accumulate a PlanningSession's fields
      one at a time, with per-field validation, and produce an
      immutable PlanningSession snapshot on build().
    - Reject duplicate Tasks (by `task_id`) before they are ever
      accumulated - Package 030's own explicit "no duplicates"
      requirement.

Non-Responsibilities:
    - PlanningSessionBuilder performs no planning, goal validation
      (in the "is this goal achievable" sense), plan optimization, or
      workflow execution - it only validates and accumulates plain
      data. "shall NOT: validate goals" refers to this broader sense;
      the type-check performed on a `with_goal()` argument below is
      construction-time input validation only, the same category of
      check every other builder/registry in this codebase performs on
      its own inputs (for example,
      DecisionEngine.register_rule()'s own isinstance check on
      `rule`), not goal-content validation.
    - This module depends on argus.planning.session (PlanningSession),
      argus.planning.metadata (PlanningMetadata),
      argus.planning.exceptions (InvalidPlanningSessionError),
      argus.planning.interfaces (IPlanningSessionBuilder),
      argus.planning.goal (PlanningGoal),
      argus.planning.constraint (PlanningConstraint),
      argus.context.context (CognitiveContext) for with_context()'s
      own type check, and argus.task.task (Task, Package 030) for
      with_task()'s own type check.

Dependencies:
    argus.planning.session (PlanningSession),
    argus.planning.metadata (PlanningMetadata),
    argus.planning.exceptions (InvalidPlanningSessionError),
    argus.planning.interfaces (IPlanningSessionBuilder),
    argus.planning.goal (PlanningGoal),
    argus.planning.constraint (PlanningConstraint),
    argus.context.context (CognitiveContext),
    argus.task.task (Task).
"""

from typing import Any, Dict, List, Optional, Sequence

from argus.context.context import CognitiveContext
from argus.planning.constraint import PlanningConstraint
from argus.planning.exceptions import InvalidPlanningSessionError
from argus.planning.goal import PlanningGoal
from argus.planning.interfaces import IPlanningSessionBuilder
from argus.planning.metadata import PlanningMetadata
from argus.planning.session import PlanningSession
from argus.task.task import Task


def _require_non_empty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidPlanningSessionError(f"{label} must be a non-empty string, got {value!r}.")
    return value


class PlanningSessionBuilder(IPlanningSessionBuilder):
    """
    A mutable, fluent builder for PlanningSession. See the module
    docstring for the full accumulation and validation semantics.
    """

    def __init__(self) -> None:
        self._cognitive_context: Optional[CognitiveContext] = None
        self._goals: List[PlanningGoal] = []
        self._constraints: List[PlanningConstraint] = []
        self._tasks: List[Task] = []
        self._metadata_extra: Dict[str, Any] = {}

    def with_context(self, cognitive_context: CognitiveContext) -> "PlanningSessionBuilder":
        if not isinstance(cognitive_context, CognitiveContext):
            raise InvalidPlanningSessionError(
                f"cognitive_context must be a CognitiveContext instance, "
                f"got {cognitive_context!r}."
            )
        self._cognitive_context = cognitive_context
        return self

    def with_goal(self, goal: PlanningGoal) -> "PlanningSessionBuilder":
        if not isinstance(goal, PlanningGoal):
            raise InvalidPlanningSessionError(
                f"goal must be a PlanningGoal instance, got {goal!r}."
            )
        self._goals.append(goal)
        return self

    def with_constraint(self, constraint: PlanningConstraint) -> "PlanningSessionBuilder":
        if not isinstance(constraint, PlanningConstraint):
            raise InvalidPlanningSessionError(
                f"constraint must be a PlanningConstraint instance, got {constraint!r}."
            )
        self._constraints.append(constraint)
        return self

    def with_task(self, task: Task) -> "PlanningSessionBuilder":
        if not isinstance(task, Task):
            raise InvalidPlanningSessionError(
                f"task must be a Task instance, got {task!r}."
            )
        if any(existing.task_id == task.task_id for existing in self._tasks):
            raise InvalidPlanningSessionError(
                f"Duplicate task_id {task.task_id!r} - a Task with this id has "
                f"already been added."
            )
        self._tasks.append(task)
        return self

    def with_tasks(self, tasks: Sequence[Task]) -> "PlanningSessionBuilder":
        if not isinstance(tasks, (list, tuple)):
            raise InvalidPlanningSessionError(
                f"tasks must be a list or tuple of Task instances, got {tasks!r}."
            )
        for task in tasks:
            self.with_task(task)
        return self

    def clear_tasks(self) -> "PlanningSessionBuilder":
        self._tasks = []
        return self

    def with_metadata(self, key: str, value: Any) -> "PlanningSessionBuilder":
        validated_key = _require_non_empty_string(key, label="metadata key")
        self._metadata_extra[validated_key] = value
        return self

    def build(self) -> PlanningSession:
        return PlanningSession(
            cognitive_context=self._cognitive_context,
            goals=tuple(self._goals),
            constraints=tuple(self._constraints),
            tasks=tuple(self._tasks),
            metadata=PlanningMetadata(extra=dict(self._metadata_extra)),
        )
