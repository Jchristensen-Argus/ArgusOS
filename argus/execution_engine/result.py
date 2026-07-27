"""
The ExecutionResult value object for the ArgusOS Execution Engine.

Purpose:
    Represent a single, immutable snapshot of one Plan having been
    processed by the Execution Engine - the Plan it covers, the
    ordered Tasks considered completed and failed, an overall
    ExecutionStatus, and descriptive metadata - per
    factory/packages/032_EXECUTION_ENGINE.md. "The Execution Engine
    accepts a Plan and produces an immutable ExecutionResult. It does
    not execute tools. It does not call APIs. It does not invoke AI.
    It simply establishes the execution lifecycle."

Every Field Defaults - ExecutionResult() Is Always Valid:
    ExecutionResult has its own dedicated ExecutionResultBuilder - the
    same "value object with a dedicated builder" shape
    CognitiveContext (022), PlanningSession (023), ExecutionTrace
    (028), Task (029), and TaskRelationship (031) all use, each of
    which lets every field default and leaves construction-time
    validation to the builder's own with_*() methods (see builder.py's
    own module docstring). `execution_id` defaults to a fresh uuid4
    string, `plan` defaults to `None` (mirroring
    `PlanningSession.cognitive_context`(022/023)/
    `TaskRelationship.source_task`(031)'s own "optional object
    reference" precedent), `completed_tasks`/`failed_tasks` both
    default to an empty tuple, `status` defaults to
    `ExecutionStatus.PENDING`, `metadata` defaults to a fresh
    `ExecutionMetadata()`. `ExecutionResult()` with no arguments is
    therefore always valid, representing an empty, not-yet-executed
    result - `ExecutionEngine.execute()` (via `ExecutionResultBuilder`)
    is the supported way to construct a genuinely populated one.

plan Holds The Object, Not A Reference String:
    Mirrors `Plan.tasks`/`PlanningSession.tasks` (030) and
    `TaskRelationship.source_task`/`target_task` (031)'s own "objects,
    not references" precedent: `plan` holds the actual, already-
    immutable `Plan` object directly - the work order's own field name
    ("plan," not "plan_id") already settles this the same way it did
    for those precedents.

completed_tasks/failed_tasks Hold Task Objects Directly, In Order:
    Both are ordered `Sequence[Task]` fields, wrapped in `tuple()` in
    `__post_init__` - the identical "wrap the given sequence in a
    tuple" pattern `Plan.steps`/`Plan.tasks` (015/030),
    `PlanningSession.goals`/`.constraints`/`.tasks` (023/030), and
    `Task.relationships` (031) all use. Unlike `Plan.tasks`/
    `Task.relationships`, this package's own Requirements list for
    ExecutionResult does not itself say "no duplicates" - "immutable,
    ordered task collections, default empty, preserve insertion
    order" is the complete list - so, unlike those two precedents,
    `ExecutionResultBuilder` performs no duplicate-`task_id` rejection
    of its own; see builder.py's own module docstring and
    factory/packages/032_EXECUTION_ENGINE.md's own Known Limitations
    for this deliberate, documented omission.

No Validation Here - See builder.py:
    Like every other value object in this codebase, ExecutionResult
    performs no validation of its own fields beyond the standard
    sequence-wrapping and `metadata` typing (an `ExecutionMetadata`,
    not a bare mapping). `ExecutionResultBuilder`'s own with_*()
    methods are where malformed input is rejected - see builder.py's
    own module docstring.

Responsibilities:
    - ExecutionResult: hold identity (`execution_id`), the `plan` it
      covers, its ordered `completed_tasks`/`failed_tasks`, an overall
      `status`, and descriptive `ExecutionMetadata`, as an immutable
      value object.

Non-Responsibilities:
    - ExecutionResult performs no reasoning, scheduling, dispatch, or
      execution of any kind - it is a record that processing occurred,
      not the processing itself. See this package's own Objective and
      Constraints.
    - This module depends only on argus.planner.plan (Plan),
      argus.task.task (Task), argus.execution_engine.status
      (ExecutionStatus), and argus.execution_engine.metadata
      (ExecutionMetadata) to type its own fields - it has no
      dependency on argus.execution_engine.engine or
      argus.execution_engine.builder, matching the "pure,
      dependency-free leaf" precedent set by every other value object
      in this codebase.

Dependencies:
    argus.planner.plan (Plan), argus.task.task (Task),
    argus.execution_engine.status (ExecutionStatus),
    argus.execution_engine.metadata (ExecutionMetadata).
"""

import uuid
from dataclasses import dataclass, field
from typing import Optional, Sequence

from argus.execution_engine.metadata import ExecutionMetadata
from argus.execution_engine.status import ExecutionStatus
from argus.planner.plan import Plan
from argus.task.task import Task


@dataclass(frozen=True)
class ExecutionResult:
    """
    An immutable snapshot of one Plan having been processed by the
    Execution Engine. See the module docstring for the full field
    semantics.

    Fields:
        execution_id: Unique identifier for this ExecutionResult.
            Defaults to a fresh uuid4 string.
        plan: The Plan this ExecutionResult covers. Defaults to None.
        completed_tasks: The ordered Tasks considered successfully
            processed. Defaults to an empty tuple. Always stored as a
            tuple, regardless of what sequence type is given.
        failed_tasks: The ordered Tasks considered unsuccessfully
            processed. Defaults to an empty tuple - always empty in
            Version 1, since "Every Task is considered successfully
            processed." Always stored as a tuple, regardless of what
            sequence type is given.
        status: This ExecutionResult's overall ExecutionStatus.
            Defaults to ExecutionStatus.PENDING.
        metadata: Descriptive bookkeeping about this ExecutionResult.
            Defaults to a fresh ExecutionMetadata.
    """

    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    plan: Optional[Plan] = None
    completed_tasks: Sequence[Task] = field(default_factory=tuple)
    failed_tasks: Sequence[Task] = field(default_factory=tuple)
    status: ExecutionStatus = ExecutionStatus.PENDING
    metadata: ExecutionMetadata = field(default_factory=ExecutionMetadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "completed_tasks", tuple(self.completed_tasks))
        object.__setattr__(self, "failed_tasks", tuple(self.failed_tasks))
