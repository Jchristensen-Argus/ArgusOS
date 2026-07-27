"""
The Task value object for the ArgusOS Task Model.

Purpose:
    Represent a single, immutable unit of work produced by a Plan -
    per factory/packages/029_TASK_MODEL.md. "A Task represents a
    single unit of work produced by a Plan. This package introduces
    no execution. Only the model." "The task contains no executable
    logic. It is purely a value object."

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
      `description`, its own `status`, and descriptive `TaskMetadata`
      as an immutable value object.

Non-Responsibilities:
    - Task performs no reasoning, scheduling, dispatch, or execution
      of any kind - see this package's own Objective and Constraints.
    - This module depends only on argus.task.status (TaskStatus) and
      argus.task.metadata (TaskMetadata) to type its own fields - it
      has no dependency on argus.task.builder, matching the "pure,
      dependency-free leaf" precedent set by every other value object
      in this codebase.

Dependencies:
    argus.task.status (TaskStatus), argus.task.metadata (TaskMetadata).
"""

import uuid
from dataclasses import dataclass, field

from argus.task.metadata import TaskMetadata
from argus.task.status import TaskStatus


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
        metadata: Descriptive bookkeeping about this Task. Defaults to
            a fresh TaskMetadata.
    """

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    metadata: TaskMetadata = field(default_factory=TaskMetadata)
