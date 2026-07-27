"""
The ExecutionResultBuilder for the ArgusOS Execution Engine.

Purpose:
    Provide a mutable, fluent way to assemble an ExecutionResult's
    fields one at a time before producing a single immutable
    ExecutionResult snapshot, per
    factory/packages/032_EXECUTION_ENGINE.md. "Builder is the only
    mutable object." Directly mirrors argus.context.builder.
    ContextBuilder (022), argus.planning.builder.PlanningSessionBuilder
    (023), argus.trace.builder.TraceBuilder (028),
    argus.task.builder.TaskBuilder (029), and
    argus.task_relationship.builder.RelationshipBuilder (031) - the
    same fluent-builder pattern applied to the Execution Engine.
    `ExecutionEngine.execute()` is this builder's own primary caller -
    see engine.py's own module docstring for how it uses this builder
    internally, mirroring `AgentService.run()`'s own identical use of
    `TraceBuilder` (028) one layer up.

with_completed_task()/with_completed_tasks()/clear_completed_tasks()
And The failed_tasks Trio Beyond The Work Order's Own Six-Item List:
    This package's own "Responsibilities" list for
    ExecutionResultBuilder names exactly six items: "assign plan,
    assign completed tasks, assign failed tasks, assign status, assign
    metadata, build immutable ExecutionResult" - one bullet each for
    "assign completed tasks"/"assign failed tasks," not three. Read
    "assign completed tasks" as the umbrella responsibility
    encompassing both a bulk-assignment method
    (`with_completed_tasks()`, matching the plural wording most
    literally) and a per-item accumulation method
    (`with_completed_task()`, matching ExecutionEngine's own "iterate
    through ordered Tasks" responsibility, which calls this method
    once per Task exactly as `AgentService.run()` calls
    `TraceBuilder.with_step()` once per stage) - the same
    "Responsibilities list under-specifies the method surface a
    builder actually needs" pattern already resolved twice (029, 031)
    for `with_name()`/`with_description()` and
    `with_source_task()`/`with_target_task()`. `clear_completed_tasks()`/
    `clear_failed_tasks()` mirror `clear_tasks()` (030)/
    `clear_relationships()` (031)'s own precedent of exposing a
    "reset this collection" method alongside the accumulate/bulk-assign
    pair. `with_failed_task()`/`with_failed_tasks()`/
    `clear_failed_tasks()` mirror the `completed_tasks` trio exactly,
    for symmetry - even though no Version 1 code ever calls
    `with_failed_task()`/`with_failed_tasks()` with a non-empty
    argument, since "Every Task is considered successfully processed."

No Duplicate-task_id Rejection - A Deliberate Difference From
Plan.tasks/Task.relationships:
    Unlike `PlanningSessionBuilder.with_task()` (030) and
    `TaskBuilder.with_relationship()` (031), neither
    `with_completed_task()` nor `with_failed_task()` rejects a
    duplicate `task_id` against what has already been accumulated.
    This package's own Requirements list for ExecutionResult reads
    "immutable, ordered task collections, default empty, preserve
    insertion order" - it does not say "no duplicates," unlike
    Package 030's own Plan.tasks Requirements list ("ordered,
    immutable, default empty, no duplicates, preserve insertion
    order") or Package 031's own Task.relationships Requirements list
    ("ordered, immutable, default empty, preserve insertion order,
    duplicate rejection in the builder"). Read literally rather than
    assumed-by-analogy: this package's own work order does not ask
    for it, so it is not added - see
    factory/packages/032_EXECUTION_ENGINE.md's own Known Limitations
    for this deliberate, documented omission, and engine.py's own
    module docstring for why it does not matter in Version 1's own
    actual call pattern (each of `plan.tasks` is placed into
    `completed_tasks` exactly once, by construction, since
    `plan.tasks` itself is already duplicate-free by the time
    `Planner`/`PlanningSessionBuilder` (030) produced it).

with_plan()/with_status() Are Singular Fields, Overwritten, Not
Accumulated:
    Each of `plan` and `status` is a single scalar field on
    ExecutionResult, not a collection - calling either method more
    than once simply overwrites the previous value, the last call
    before build() wins. Mirrors TaskBuilder.with_status()'s own
    identical "singular field is overwritten" rule.

with_metadata() Only Ever Populates `extra`:
    ExecutionMetadata's `created_at`, `version`, and `correlation_id`
    fields are system-assigned at ExecutionResult construction time
    (see metadata.py's own module docstring) - ExecutionResultBuilder
    exposes no way to override them. with_metadata(key, value) adds
    one key/value pair to the eventual ExecutionMetadata.extra
    mapping; calling it multiple times with different keys
    accumulates, and calling it twice with the same key overwrites
    that key's value - the last call wins, mirroring
    ContextBuilder/PlanningSessionBuilder/TraceBuilder/TaskBuilder/
    RelationshipBuilder's identical rule.

Validation Lives Here, Not On ExecutionResult:
    See result.py's own module docstring - ExecutionResult performs
    no validation of its own; every `with_*` method below validates
    its argument before assigning/accumulating it, raising
    InvalidExecutionResultError for malformed input. build() itself
    performs no additional validation - by the time build() runs,
    every assigned value has already been validated at the point it
    was set. An ExecutionResult built via ExecutionResultBuilder
    without ever calling with_plan() still has `plan=None` - the
    empty default, not an error.

Independent Snapshots:
    build() constructs a fresh ExecutionResult (and a fresh
    ExecutionMetadata) from this builder's current accumulated state
    every time it is called. Continuing to call `with_*` methods on
    the same builder after calling build() - or calling build() more
    than once - never mutates an ExecutionResult already returned by
    an earlier build() call, since ExecutionResult itself is immutable
    and each build() call constructs a fresh instance.

Responsibilities:
    - ExecutionResultBuilder: assign an ExecutionResult's fields one
      at a time, with per-field validation, accumulate its ordered
      `completed_tasks`/`failed_tasks`, and produce an immutable
      ExecutionResult snapshot on build().

Non-Responsibilities:
    - ExecutionResultBuilder performs no reasoning, scheduling,
      dispatch, or execution of any kind - it only validates and
      assigns plain data.
    - ExecutionResultBuilder is not a service - see interfaces.py's
      own module docstring.

Dependencies:
    argus.planner.plan (Plan), argus.task.task (Task),
    argus.execution_engine.result (ExecutionResult),
    argus.execution_engine.status (ExecutionStatus),
    argus.execution_engine.metadata (ExecutionMetadata),
    argus.execution_engine.exceptions (InvalidExecutionResultError),
    argus.execution_engine.interfaces (IExecutionResultBuilder).
"""

from typing import Any, Dict, List, Sequence

from argus.execution_engine.exceptions import InvalidExecutionResultError
from argus.execution_engine.interfaces import IExecutionResultBuilder
from argus.execution_engine.metadata import ExecutionMetadata
from argus.execution_engine.result import ExecutionResult
from argus.execution_engine.status import ExecutionStatus
from argus.planner.plan import Plan
from argus.task.task import Task


def _require_non_empty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidExecutionResultError(
            f"{label} must be a non-empty string, got {value!r}."
        )
    return value


class ExecutionResultBuilder(IExecutionResultBuilder):
    """
    A mutable, fluent builder for ExecutionResult. See the module
    docstring for the full assignment and validation semantics.
    """

    def __init__(self) -> None:
        self._plan = None
        self._completed_tasks: List[Task] = []
        self._failed_tasks: List[Task] = []
        self._status: ExecutionStatus = ExecutionStatus.PENDING
        self._metadata_extra: Dict[str, Any] = {}

    def with_plan(self, plan: Plan) -> "ExecutionResultBuilder":
        if not isinstance(plan, Plan):
            raise InvalidExecutionResultError(
                f"plan must be a Plan instance, got {plan!r}."
            )
        self._plan = plan
        return self

    def with_completed_task(self, task: Task) -> "ExecutionResultBuilder":
        if not isinstance(task, Task):
            raise InvalidExecutionResultError(
                f"task must be a Task instance, got {task!r}."
            )
        self._completed_tasks.append(task)
        return self

    def with_completed_tasks(self, tasks: Sequence[Task]) -> "ExecutionResultBuilder":
        if not isinstance(tasks, (list, tuple)):
            raise InvalidExecutionResultError(
                f"tasks must be a list or tuple of Task instances, got {tasks!r}."
            )
        for task in tasks:
            self.with_completed_task(task)
        return self

    def clear_completed_tasks(self) -> "ExecutionResultBuilder":
        self._completed_tasks = []
        return self

    def with_failed_task(self, task: Task) -> "ExecutionResultBuilder":
        if not isinstance(task, Task):
            raise InvalidExecutionResultError(
                f"task must be a Task instance, got {task!r}."
            )
        self._failed_tasks.append(task)
        return self

    def with_failed_tasks(self, tasks: Sequence[Task]) -> "ExecutionResultBuilder":
        if not isinstance(tasks, (list, tuple)):
            raise InvalidExecutionResultError(
                f"tasks must be a list or tuple of Task instances, got {tasks!r}."
            )
        for task in tasks:
            self.with_failed_task(task)
        return self

    def clear_failed_tasks(self) -> "ExecutionResultBuilder":
        self._failed_tasks = []
        return self

    def with_status(self, status: ExecutionStatus) -> "ExecutionResultBuilder":
        if not isinstance(status, ExecutionStatus):
            raise InvalidExecutionResultError(
                f"status must be an ExecutionStatus instance, got {status!r}."
            )
        self._status = status
        return self

    def with_metadata(self, key: str, value: Any) -> "ExecutionResultBuilder":
        validated_key = _require_non_empty_string(key, label="metadata key")
        self._metadata_extra[validated_key] = value
        return self

    def build(self) -> ExecutionResult:
        return ExecutionResult(
            plan=self._plan,
            completed_tasks=tuple(self._completed_tasks),
            failed_tasks=tuple(self._failed_tasks),
            status=self._status,
            metadata=ExecutionMetadata(extra=dict(self._metadata_extra)),
        )
