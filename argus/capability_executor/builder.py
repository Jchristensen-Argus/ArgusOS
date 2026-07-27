"""
The CapabilityExecutionResultBuilder for the ArgusOS Capability
Executor.

Purpose:
    Provide a mutable, fluent way to assemble a
    CapabilityExecutionResult's fields one at a time before producing
    a single immutable CapabilityExecutionResult snapshot, per
    factory/packages/034_CAPABILITY_EXECUTOR.md. "Builder is the only
    mutable object." Directly mirrors argus.context.builder.
    ContextBuilder (022), argus.planning.builder.PlanningSessionBuilder
    (023), argus.trace.builder.TraceBuilder (028), argus.task.builder.
    TaskBuilder (029), argus.task_relationship.builder.
    RelationshipBuilder (031), argus.execution_engine.builder.
    ExecutionResultBuilder (032), and argus.capability.builder.
    CapabilityBuilder (033) - the same fluent-builder pattern applied
    to the Capability Executor. `CapabilityExecutor.resolve()` is this
    builder's own primary caller - see executor.py's own module
    docstring for how it uses this builder internally.

No with_execution_id() - Identity Is Always System-Assigned:
    This package's own "Responsibilities" list for
    CapabilityExecutionResultBuilder names exactly five items: "assign
    task, assign capability, assign status, assign metadata, build
    immutable result" - no "assign execution_id." Unlike
    CapabilityBuilder (033), whose own Responsibilities list
    explicitly names "assign id" (a deliberate, documented divergence
    from every other builder in this codebase), this package's own
    list matches RelationshipBuilder's (031) and
    ExecutionResultBuilder's (032) own shape exactly - neither of
    which exposes a way to set the built object's own auto-generated
    identity field. `execution_id` is therefore always system-assigned
    via CapabilityExecutionResult's own `default_factory`, matching
    the majority precedent this codebase's builders establish.

with_task()/with_capability()/with_status() Are Singular Fields,
Overwritten, Not Accumulated:
    Each of `task`, `capability`, and `status` is a single scalar
    field on CapabilityExecutionResult, not a collection - calling any
    of them more than once simply overwrites the previous value, the
    last call before build() wins. Mirrors ExecutionResultBuilder.
    with_plan()/with_status()'s own identical "singular field is
    overwritten" rule.

with_capability() Requires An Actual Capability Instance - No None
Shortcut:
    Mirrors ExecutionResultBuilder.with_plan()'s own identical rule:
    `with_capability()` raises InvalidCapabilityExecutionResultError if
    given anything other than a Capability instance, including None.
    A CapabilityExecutionResult with `capability=None` (the NOT_FOUND
    case) is produced simply by never calling with_capability() at
    all, leaving the field at its own default - not by calling
    with_capability(None).

with_metadata() Only Ever Populates `extra`:
    CapabilityExecutionMetadata's `created_at`, `version`, and
    `correlation_id` fields are system-assigned at
    CapabilityExecutionResult construction time (see metadata.py's own
    module docstring) - CapabilityExecutionResultBuilder exposes no
    way to override them. with_metadata(key, value) adds one
    key/value pair to the eventual CapabilityExecutionMetadata.extra
    mapping; calling it multiple times with different keys
    accumulates, and calling it twice with the same key overwrites
    that key's value - the last call wins, mirroring every sibling
    builder's identical rule.

Validation Lives Here, Not On CapabilityExecutionResult:
    See result.py's own module docstring -
    CapabilityExecutionResult performs no validation of its own; every
    `with_*` method below validates its argument before assigning it,
    raising InvalidCapabilityExecutionResultError for malformed input.
    build() itself performs no additional validation - by the time
    build() runs, every assigned value has already been validated at
    the point it was set.

Independent Snapshots:
    build() constructs a fresh CapabilityExecutionResult (and a fresh
    CapabilityExecutionMetadata) from this builder's current
    accumulated state every time it is called. Continuing to call
    `with_*` methods on the same builder after calling build() - or
    calling build() more than once - never mutates a
    CapabilityExecutionResult already returned by an earlier build()
    call, since CapabilityExecutionResult itself is immutable and each
    build() call constructs a fresh instance.

Responsibilities:
    - CapabilityExecutionResultBuilder: assign a
      CapabilityExecutionResult's fields one at a time, with per-field
      validation, and produce an immutable CapabilityExecutionResult
      snapshot on build().

Non-Responsibilities:
    - CapabilityExecutionResultBuilder performs no reasoning,
      dispatch, or execution of any kind - it only validates and
      assigns plain data.
    - CapabilityExecutionResultBuilder is not a service - see
      interfaces.py's own module docstring.

Dependencies:
    argus.task.task (Task), argus.capability.capability (Capability),
    argus.capability_executor.result (CapabilityExecutionResult),
    argus.capability_executor.status (CapabilityExecutionStatus),
    argus.capability_executor.metadata (CapabilityExecutionMetadata),
    argus.capability_executor.exceptions
    (InvalidCapabilityExecutionResultError),
    argus.capability_executor.interfaces
    (ICapabilityExecutionResultBuilder).
"""

from typing import Any, Dict, Optional

from argus.capability.capability import Capability
from argus.capability_executor.exceptions import InvalidCapabilityExecutionResultError
from argus.capability_executor.interfaces import ICapabilityExecutionResultBuilder
from argus.capability_executor.metadata import CapabilityExecutionMetadata
from argus.capability_executor.result import CapabilityExecutionResult
from argus.capability_executor.status import CapabilityExecutionStatus
from argus.task.task import Task


def _require_non_empty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidCapabilityExecutionResultError(
            f"{label} must be a non-empty string, got {value!r}."
        )
    return value


class CapabilityExecutionResultBuilder(ICapabilityExecutionResultBuilder):
    """
    A mutable, fluent builder for CapabilityExecutionResult. See the
    module docstring for the full assignment and validation semantics.
    """

    def __init__(self) -> None:
        self._task: Optional[Task] = None
        self._capability: Optional[Capability] = None
        self._status: CapabilityExecutionStatus = CapabilityExecutionStatus.PENDING
        self._metadata_extra: Dict[str, Any] = {}

    def with_task(self, task: Task) -> "CapabilityExecutionResultBuilder":
        if not isinstance(task, Task):
            raise InvalidCapabilityExecutionResultError(
                f"task must be a Task instance, got {task!r}."
            )
        self._task = task
        return self

    def with_capability(self, capability: Capability) -> "CapabilityExecutionResultBuilder":
        if not isinstance(capability, Capability):
            raise InvalidCapabilityExecutionResultError(
                f"capability must be a Capability instance, got {capability!r}."
            )
        self._capability = capability
        return self

    def with_status(
        self, status: CapabilityExecutionStatus
    ) -> "CapabilityExecutionResultBuilder":
        if not isinstance(status, CapabilityExecutionStatus):
            raise InvalidCapabilityExecutionResultError(
                f"status must be a CapabilityExecutionStatus instance, got {status!r}."
            )
        self._status = status
        return self

    def with_metadata(self, key: str, value: Any) -> "CapabilityExecutionResultBuilder":
        validated_key = _require_non_empty_string(key, label="metadata key")
        self._metadata_extra[validated_key] = value
        return self

    def build(self) -> CapabilityExecutionResult:
        return CapabilityExecutionResult(
            task=self._task,
            capability=self._capability,
            status=self._status,
            metadata=CapabilityExecutionMetadata(extra=dict(self._metadata_extra)),
        )
