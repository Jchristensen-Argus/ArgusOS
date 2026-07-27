"""
The Task value object for the ArgusOS Task Model.

Purpose:
    Represent a single, immutable unit of work produced by a Plan -
    per factory/packages/029_TASK_MODEL.md, as amended by
    factory/packages/031_TASK_RELATIONSHIPS.md. "A Task represents a
    single unit of work produced by a Plan. This package introduces
    no execution. Only the model." "The task contains no executable
    logic. It is purely a value object."

Package 031 Amendment - relationships Joins task_id/name/description/
status:
    Per this package's own "New architecture" diagram - "Plan ->
    Tasks -> Relationships" - Task gained a fifth field,
    `relationships: Sequence[TaskRelationship]`, holding the immutable
    `TaskRelationship` objects (Package 031) this Task has been given,
    defaulting to an empty tuple, ordered, duplicate-free by
    `relationship_id`. Declared after `status` and before `metadata` -
    continuing Package 030's own "insert the new collection field
    before metadata, so metadata stays the last-declared field"
    precedent (Plan.tasks/PlanningSession.tasks) exactly. Task never
    generates, decomposes, or validates the TaskRelationships it is
    given - see builder.py's own module docstring for where
    `with_relationship()`/`with_relationships()`'s
    duplicate-`relationship_id` validation actually lives.

Avoiding A Circular Import - TYPE_CHECKING Only:
    `argus.task_relationship.relationship.TaskRelationship` itself
    depends on `argus.task.task.Task` (for its own
    `source_task`/`target_task` fields) - a real, unavoidable
    dependency, since a relationship is meaningless without the Tasks
    it connects. For `Task.relationships` to be typed as
    `Sequence[TaskRelationship]` without creating a genuine circular
    import, this module imports `TaskRelationship` only under
    `typing.TYPE_CHECKING` (never evaluated at runtime) and spells the
    field's own annotation as a forward-reference string,
    `Sequence["TaskRelationship"]`. `argus.task.builder` (which needs
    `TaskRelationship` for real, runtime `isinstance()` validation)
    imports it directly - that import is not circular, since
    `argus.task.task` never imports `argus.task.builder` and
    `argus.task_relationship.relationship` never imports
    `argus.task.builder` either.

Every Field Defaults - Task() Is Always Valid:
    Unlike PlanStep (constructed directly by Planner.add_step(), with
    no builder of its own, and therefore required, no-default
    `description`/`required_capability` fields), Task has its own
    dedicated TaskBuilder - the same "value object with a dedicated
    builder" shape CognitiveContext (022), PlanningSession (023), and
    ExecutionTrace (028) all use, each of which lets every field
    default and leaves construction-time validation to the builder's
    own with_*() methods (see builder.py's own module docstring).
    `task_id` defaults to a fresh uuid4 string, `name` and
    `description` both default to `""`, `status` defaults to
    `TaskStatus.PENDING`, `metadata` defaults to a fresh
    `TaskMetadata()`. `Task()` with no arguments is therefore always
    valid, representing an empty, unnamed task - `TaskBuilder` is the
    supported way to construct a genuinely populated one.

No Validation Here - See builder.py:
    Like every other value object in this codebase, Task performs no
    validation of its own fields in `__post_init__` beyond the
    standard `metadata` typing (a `TaskMetadata`, not a bare mapping).
    `TaskBuilder`'s own `with_name()`/`with_description()`/
    `with_status()`/`with_metadata()` methods are where malformed
    input is rejected - see builder.py's own module docstring.

Responsibilities:
    - Task: hold identity (`task_id`), a human-readable `name` and
      `description`, its own `status`, descriptive `TaskMetadata`, and
      its own ordered `relationships` (Package 031), as an immutable
      value object.

Non-Responsibilities:
    - Task performs no reasoning, scheduling, dispatch, or execution
      of any kind - see this package's own Objective and Constraints.
    - Task performs no duplicate-`relationship_id` rejection of its
      own - see builder.py's own module docstring for where that
      validation lives.
    - This module depends on argus.task.status (TaskStatus) and
      argus.task.metadata (TaskMetadata) to type its own fields, and
      on argus.task_relationship.relationship (TaskRelationship) for
      typing only (TYPE_CHECKING-guarded, never imported at runtime -
      see the "Avoiding A Circular Import" note above). It has no
      runtime dependency on argus.task.builder or
      argus.task_relationship.builder, matching the "pure,
      dependency-free leaf" precedent set by every other value object
      in this codebase.

Dependencies:
    argus.task.status (TaskStatus), argus.task.metadata (TaskMetadata),
    argus.task_relationship.relationship (TaskRelationship) - Package
    031, typing only.
"""

import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Sequence

from argus.task.metadata import TaskMetadata
from argus.task.status import TaskStatus

if TYPE_CHECKING:
    from argus.task_relationship.relationship import TaskRelationship


@dataclass(frozen=True)
class Task:
    """
    An immutable record of one unit of work produced by a Plan. See
    the module docstring for the full field semantics.

    Fields:
        task_id: Unique identifier for this Task. Defaults to a fresh
            uuid4 string.
        name: A short, human-readable label for this Task. Defaults
            to an empty string.
        description: A longer, human-readable elaboration of what
            this Task represents. Defaults to an empty string.
        status: This Task's current TaskStatus. Defaults to
            TaskStatus.PENDING.
        relationships: The ordered TaskRelationship objects describing
            this Task's relationships with other Tasks (Package 031).
            Defaults to an empty tuple. Always stored as a tuple,
            regardless of what sequence type is given.
        metadata: Descriptive bookkeeping about this Task. Defaults to
            a fresh TaskMetadata.
    """

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    relationships: Sequence["TaskRelationship"] = field(default_factory=tuple)
    metadata: TaskMetadata = field(default_factory=TaskMetadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "relationships", tuple(self.relationships))
