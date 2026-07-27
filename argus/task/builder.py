"""
The TaskBuilder for the ArgusOS Task Model.

Purpose:
    Provide a mutable, fluent way to assemble a Task's fields one at a
    time before producing a single immutable Task snapshot, per
    factory/packages/029_TASK_MODEL.md, as amended by
    factory/packages/031_TASK_RELATIONSHIPS.md. "Builder is the only
    mutable object." Directly mirrors argus.context.builder.
    ContextBuilder (022), argus.planning.builder.PlanningSessionBuilder
    (023), and argus.trace.builder.TraceBuilder (028) - the same
    fluent-builder pattern applied to the Task Model.

Package 031 Amendment - with_relationship()/with_relationships()/
clear_relationships():
    TaskBuilder gained three new methods, mirroring
    PlanningSessionBuilder's own identically-shaped
    with_task()/with_tasks()/clear_tasks() (Package 030) one layer
    down: `with_relationship(relationship)` validates the argument is
    a TaskRelationship, rejects a duplicate `relationship_id` against
    every TaskRelationship already accumulated (identity-based
    duplicate detection, the same policy Package 030 applied to
    Plan.tasks/PlanningSession.tasks), then appends;
    `with_relationships(relationships)` validates the argument is a
    list or tuple, then delegates to `with_relationship()` once per
    item, in order - not a parallel validation path, so duplicate
    rejection (within the batch, and against anything already
    accumulated) is inherited automatically; `clear_relationships()`
    resets the accumulated relationship list to empty, mirroring
    `clear_tasks()`'s own precedent as "the first 'reset a
    collection' method any builder in this codebase has ever
    exposed" for this particular field.

Responsibilities Beyond The Work Order's Own Four-Item List:
    This package's own "Responsibilities" list for TaskBuilder names
    exactly four items: "create task, assign metadata, assign status,
    build immutable Task" - it does not separately name "assign
    name"/"assign description" as their own bullets. Read "create
    task" as the umbrella responsibility encompassing a Task's basic
    identity (`name`/`description`), the same way every other
    fluent builder in this codebase (ContextBuilder, PlanningSessionBuilder,
    TraceBuilder) exposes a `with_*()` method for every field its
    built object holds, not only the fields a work order happened to
    call out individually - a builder that could not actually set
    `name`/`description` would leave `Task.name`/`Task.description`
    permanently stuck at their own empty-string defaults for any
    caller using the supported construction path. `with_name()` and
    `with_description()` are therefore included alongside
    `with_status()`/`with_metadata()`/`build()`.

with_name() / with_description() / with_status() Are Singular Fields,
Overwritten, Not Accumulated:
    Each of `name`, `description`, and `status` is a single scalar
    field on `Task`, not a collection - calling `with_name()` (or
    `with_description()`/`with_status()`) more than once simply
    overwrites the previous value, the last call before build() wins.
    This mirrors ContextBuilder.with_conversation()/
    PlanningSessionBuilder.with_context()'s own identical
    "singular field is overwritten" rule.

with_metadata() Only Ever Populates `extra`:
    TaskMetadata's `created_at`, `version`, and `correlation_id`
    fields are system-assigned at Task construction time (see
    metadata.py's own module docstring) - TaskBuilder exposes no way
    to override them. with_metadata(key, value) adds one key/value
    pair to the eventual TaskMetadata.extra mapping; calling it
    multiple times with different keys accumulates, and calling it
    twice with the same key overwrites that key's value - the last
    call wins, mirroring ContextBuilder/PlanningSessionBuilder/
    TraceBuilder's identical rule.

Validation Lives Here, Not On Task:
    See task.py's own module docstring - Task performs no validation
    of its own; every `with_*` method below validates its argument
    before assigning/accumulating it, raising InvalidTaskError for
    malformed input. build() itself performs no additional validation
    - by the time build() runs, every assigned value has already been
    validated at the point it was set. Unlike Task's own all-defaulted
    fields, this means a Task built via TaskBuilder without ever
    calling with_name() still has `name=""` - the empty default, not
    an error; TaskBuilder validates the *shape* of what it is given
    (a string, a TaskStatus instance), not whether every field was
    ever set at all.

Independent Snapshots:
    build() constructs a fresh Task (and a fresh TaskMetadata) from
    this builder's current accumulated state every time it is called.
    Continuing to call `with_*` methods on the same builder after
    calling build() - or calling build() more than once - never
    mutates a Task already returned by an earlier build() call, since
    Task itself is immutable and each build() call constructs a fresh
    instance.

Responsibilities:
    - TaskBuilder: assign a Task's fields one at a time, with
      per-field validation, accumulate its ordered `relationships`
      (Package 031), and produce an immutable Task snapshot on
      build().

Non-Responsibilities:
    - TaskBuilder performs no reasoning, scheduling, dispatch, or
      execution of any kind - it only validates and assigns plain
      data.
    - TaskBuilder is not a service - see interfaces.py's own module
      docstring.

Dependencies:
    argus.task.task (Task), argus.task.status (TaskStatus),
    argus.task.metadata (TaskMetadata), argus.task.exceptions
    (InvalidTaskError), argus.task.interfaces (ITaskBuilder),
    argus.task_relationship.relationship (TaskRelationship) - Package
    031, for with_relationship()/with_relationships()'s own runtime
    isinstance() validation. Not circular: argus.task.task never
    imports argus.task_relationship.relationship at runtime (see
    task.py's own "Avoiding A Circular Import" note), and
    argus.task_relationship.relationship never imports
    argus.task.builder.
"""

from typing import Any, Dict, List, Sequence

from argus.task.exceptions import InvalidTaskError
from argus.task.interfaces import ITaskBuilder
from argus.task.metadata import TaskMetadata
from argus.task.status import TaskStatus
from argus.task.task import Task
from argus.task_relationship.relationship import TaskRelationship


def _require_non_empty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidTaskError(f"{label} must be a non-empty string, got {value!r}.")
    return value


class TaskBuilder(ITaskBuilder):
    """
    A mutable, fluent builder for Task. See the module docstring for
    the full assignment and validation semantics.
    """

    def __init__(self) -> None:
        self._name: str = ""
        self._description: str = ""
        self._status: TaskStatus = TaskStatus.PENDING
        self._relationships: List[TaskRelationship] = []
        self._metadata_extra: Dict[str, Any] = {}

    def with_name(self, name: str) -> "TaskBuilder":
        self._name = _require_non_empty_string(name, label="name")
        return self

    def with_description(self, description: str) -> "TaskBuilder":
        if not isinstance(description, str):
            raise InvalidTaskError(
                f"description must be a string, got {description!r}."
            )
        self._description = description
        return self

    def with_status(self, status: TaskStatus) -> "TaskBuilder":
        if not isinstance(status, TaskStatus):
            raise InvalidTaskError(
                f"status must be a TaskStatus instance, got {status!r}."
            )
        self._status = status
        return self

    def with_relationship(self, relationship: TaskRelationship) -> "TaskBuilder":
        if not isinstance(relationship, TaskRelationship):
            raise InvalidTaskError(
                f"relationship must be a TaskRelationship instance, "
                f"got {relationship!r}."
            )
        if any(
            existing.relationship_id == relationship.relationship_id
            for existing in self._relationships
        ):
            raise InvalidTaskError(
                f"Duplicate relationship_id {relationship.relationship_id!r} - a "
                f"TaskRelationship with this id has already been added."
            )
        self._relationships.append(relationship)
        return self

    def with_relationships(self, relationships: Sequence[TaskRelationship]) -> "TaskBuilder":
        if not isinstance(relationships, (list, tuple)):
            raise InvalidTaskError(
                f"relationships must be a list or tuple of TaskRelationship "
                f"instances, got {relationships!r}."
            )
        for relationship in relationships:
            self.with_relationship(relationship)
        return self

    def clear_relationships(self) -> "TaskBuilder":
        self._relationships = []
        return self

    def with_metadata(self, key: str, value: Any) -> "TaskBuilder":
        validated_key = _require_non_empty_string(key, label="metadata key")
        self._metadata_extra[validated_key] = value
        return self

    def build(self) -> Task:
        return Task(
            name=self._name,
            description=self._description,
            status=self._status,
            relationships=tuple(self._relationships),
            metadata=TaskMetadata(extra=dict(self._metadata_extra)),
        )
