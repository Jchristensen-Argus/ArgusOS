"""
The CapabilityExecutionResult value object for the ArgusOS Capability
Executor.

Purpose:
    Represent a single, immutable snapshot of one Task having been
    resolved against the Capability Registry by the Capability
    Executor - the Task considered, the Capability found (if any), an
    overall CapabilityExecutionStatus, and descriptive metadata - per
    factory/packages/034_CAPABILITY_EXECUTOR.md. "The Capability
    Executor resolves a Capability for a Task and produces an
    immutable CapabilityExecutionResult."

Every Field Defaults - CapabilityExecutionResult() Is Always Valid:
    CapabilityExecutionResult has its own dedicated
    CapabilityExecutionResultBuilder - the same "value object with a
    dedicated builder" shape CognitiveContext (022), PlanningSession
    (023), ExecutionTrace (028), Task (029), TaskRelationship (031),
    and ExecutionResult (032) all use, each of which lets every field
    default and leaves construction-time validation to the builder's
    own with_*() methods (see builder.py's own module docstring).
    `execution_id` defaults to a fresh uuid4 string, `task` and
    `capability` both default to `None` (mirroring
    `ExecutionResult.plan`(032)/`PlanningSession.cognitive_context`
    (022/023)/`TaskRelationship.source_task`(031)'s own "optional
    object reference" precedent), `status` defaults to
    `CapabilityExecutionStatus.PENDING`, `metadata` defaults to a
    fresh `CapabilityExecutionMetadata()`.
    `CapabilityExecutionResult()` with no arguments is therefore
    always valid, representing an empty, not-yet-resolved result -
    `CapabilityExecutor.resolve()` (via
    `CapabilityExecutionResultBuilder`) is the supported way to
    construct a genuinely populated one.

task/capability Hold The Objects Directly, Not Reference Strings:
    Mirrors `ExecutionResult.plan` (032) and
    `TaskRelationship.source_task`/`target_task` (031)'s own "objects,
    not references" precedent: `task` and `capability` hold the
    actual, already-immutable `Task`/`Capability` objects directly -
    the work order's own field names ("task," "capability," not
    "task_id," "capability_id") already settle this the same way they
    did for those precedents. `capability` is `None` whenever no
    matching Capability was found - the NOT_FOUND case never fabricates
    a placeholder Capability.

Field Order Matches The Work Order's Own Literal Listing:
    "Fields: execution_id, task, capability, status, metadata" -
    unlike the metadata-field-order tension Packages 028/029/031/032/
    033 each had to resolve, this package's own literal field order
    already places `metadata` last and needs no normalization.

No Validation Here - See builder.py:
    Like every other value object in this codebase,
    CapabilityExecutionResult performs no validation of its own
    fields beyond `metadata`'s own typing (a CapabilityExecutionMetadata,
    not a bare mapping). CapabilityExecutionResultBuilder's own
    with_*() methods are where malformed input is rejected - see
    builder.py's own module docstring.

Responsibilities:
    - CapabilityExecutionResult: hold identity (`execution_id`), the
      `task` considered, the `capability` found (if any), an overall
      `status`, and descriptive `CapabilityExecutionMetadata`, as an
      immutable value object.

Non-Responsibilities:
    - CapabilityExecutionResult performs no reasoning, dispatch, or
      execution of any kind - it is a record that resolution was
      attempted, not the resolution itself. See this package's own
      Objective and Constraints.
    - This module depends only on argus.task.task (Task),
      argus.capability.capability (Capability),
      argus.capability_executor.status (CapabilityExecutionStatus),
      and argus.capability_executor.metadata
      (CapabilityExecutionMetadata) to type its own fields - it has no
      dependency on argus.capability_executor.executor or
      argus.capability_executor.builder, matching the "pure,
      dependency-free leaf" precedent set by every other value object
      in this codebase.

Dependencies:
    argus.task.task (Task), argus.capability.capability (Capability),
    argus.capability_executor.status (CapabilityExecutionStatus),
    argus.capability_executor.metadata (CapabilityExecutionMetadata).
"""

import uuid
from dataclasses import dataclass, field
from typing import Optional

from argus.capability.capability import Capability
from argus.capability_executor.metadata import CapabilityExecutionMetadata
from argus.capability_executor.status import CapabilityExecutionStatus
from argus.task.task import Task


@dataclass(frozen=True)
class CapabilityExecutionResult:
    """
    An immutable snapshot of one Task having been resolved against the
    Capability Registry. See the module docstring for the full field
    semantics.

    Fields:
        execution_id: Unique identifier for this
            CapabilityExecutionResult. Defaults to a fresh uuid4
            string.
        task: The Task this CapabilityExecutionResult covers. Defaults
            to None.
        capability: The Capability found for `task`, if any. Defaults
            to None - always None when `status` is NOT_FOUND.
        status: This CapabilityExecutionResult's overall
            CapabilityExecutionStatus. Defaults to
            CapabilityExecutionStatus.PENDING.
        metadata: Descriptive bookkeeping about this
            CapabilityExecutionResult. Defaults to a fresh
            CapabilityExecutionMetadata.
    """

    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task: Optional[Task] = None
    capability: Optional[Capability] = None
    status: CapabilityExecutionStatus = CapabilityExecutionStatus.PENDING
    metadata: CapabilityExecutionMetadata = field(default_factory=CapabilityExecutionMetadata)
