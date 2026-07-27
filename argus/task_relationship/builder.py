"""
The RelationshipBuilder for the ArgusOS Task Relationships package.

Purpose:
    Provide a mutable, fluent way to assemble a TaskRelationship's
    fields one at a time before producing a single immutable
    TaskRelationship snapshot, per
    factory/packages/031_TASK_RELATIONSHIPS.md. "Builder is the only
    mutable object." Directly mirrors argus.context.builder.
    ContextBuilder (022), argus.planning.builder.PlanningSessionBuilder
    (023), argus.trace.builder.TraceBuilder (028), and
    argus.task.builder.TaskBuilder (029) - the same fluent-builder
    pattern applied to the Task Relationships model.

with_source_task()/with_target_task() Beyond The Work Order's Own
Four-Item List:
    This package's own "Responsibilities" list for RelationshipBuilder
    names exactly four items: "create relationship, assign metadata,
    assign type, build immutable TaskRelationship" - it does not
    separately name "assign source_task"/"assign target_task" as
    their own bullets. This is the identical shape of gap Package 029
    faced with TaskBuilder's own "create task" bullet omitting
    "assign name"/"assign description" - resolved the same way here:
    "create relationship" is read as the umbrella responsibility
    encompassing a TaskRelationship's own two Task references, since a
    builder that could never set source_task/target_task away from
    their own None defaults could not actually build a meaningful
    relationship at all. `with_source_task()`/`with_target_task()` are
    therefore included alongside `with_type()`/`with_metadata()`/
    `build()`. See relationship.py's own module docstring and
    factory/packages/031_TASK_RELATIONSHIPS.md's own "Engineering
    Decision" section for the full reasoning.

with_source_task()/with_target_task()/with_type() Are Singular Fields,
Overwritten, Not Accumulated:
    Each of `source_task`, `target_task`, and `relationship_type` is a
    single scalar field on TaskRelationship, not a collection -
    calling any of these methods more than once simply overwrites the
    previous value, the last call before build() wins. Mirrors
    TaskBuilder.with_status()'s own identical "singular field is
    overwritten" rule.

with_metadata() Only Ever Populates `extra`:
    RelationshipMetadata's `created_at`, `version`, and
    `correlation_id` fields are system-assigned at TaskRelationship
    construction time (see metadata.py's own module docstring) -
    RelationshipBuilder exposes no way to override them.
    with_metadata(key, value) adds one key/value pair to the eventual
    RelationshipMetadata.extra mapping; calling it multiple times with
    different keys accumulates, and calling it twice with the same
    key overwrites that key's value - the last call wins, mirroring
    ContextBuilder/PlanningSessionBuilder/TraceBuilder/TaskBuilder's
    identical rule.

No Same-Task Validation:
    with_source_task()/with_target_task() validate only that the
    given argument is a Task instance - neither method checks it
    against the builder's own already-set source_task/target_task, so
    a RelationshipBuilder may produce a TaskRelationship whose
    source_task and target_task are the very same Task. "Do not
    interpret them. Do not infer behavior" - this package draws no
    conclusion from that case being unusual; see
    factory/packages/031_TASK_RELATIONSHIPS.md's own Known
    Limitations.

Validation Lives Here, Not On TaskRelationship:
    See relationship.py's own module docstring - TaskRelationship
    performs no validation of its own; every `with_*` method below
    validates its argument before assigning/accumulating it, raising
    InvalidTaskRelationshipError for malformed input. build() itself
    performs no additional validation - by the time build() runs,
    every assigned value has already been validated at the point it
    was set. A TaskRelationship built via RelationshipBuilder without
    ever calling with_source_task()/with_target_task() still has
    `source_task=None`/`target_task=None` - the empty default, not an
    error.

Independent Snapshots:
    build() constructs a fresh TaskRelationship (and a fresh
    RelationshipMetadata) from this builder's current accumulated
    state every time it is called. Continuing to call `with_*` methods
    on the same builder after calling build() - or calling build()
    more than once - never mutates a TaskRelationship already returned
    by an earlier build() call, since TaskRelationship itself is
    immutable and each build() call constructs a fresh instance.

Responsibilities:
    - RelationshipBuilder: assign a TaskRelationship's fields one at a
      time, with per-field validation, and produce an immutable
      TaskRelationship snapshot on build().

Non-Responsibilities:
    - RelationshipBuilder performs no scheduling, dependency
      resolution, ordering, or execution of any kind - it only
      validates and assigns plain data.
    - RelationshipBuilder is not a service - see interfaces.py's own
      module docstring.

Dependencies:
    argus.task.task (Task), argus.task_relationship.relationship
    (TaskRelationship), argus.task_relationship.relationship_type
    (RelationshipType), argus.task_relationship.metadata
    (RelationshipMetadata), argus.task_relationship.exceptions
    (InvalidTaskRelationshipError), argus.task_relationship.interfaces
    (IRelationshipBuilder).
"""

from typing import Any, Dict

from argus.task.task import Task
from argus.task_relationship.exceptions import InvalidTaskRelationshipError
from argus.task_relationship.interfaces import IRelationshipBuilder
from argus.task_relationship.metadata import RelationshipMetadata
from argus.task_relationship.relationship import TaskRelationship
from argus.task_relationship.relationship_type import RelationshipType


def _require_non_empty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidTaskRelationshipError(
            f"{label} must be a non-empty string, got {value!r}."
        )
    return value


class RelationshipBuilder(IRelationshipBuilder):
    """
    A mutable, fluent builder for TaskRelationship. See the module
    docstring for the full assignment and validation semantics.
    """

    def __init__(self) -> None:
        self._source_task = None
        self._target_task = None
        self._relationship_type: RelationshipType = RelationshipType.RELATED
        self._metadata_extra: Dict[str, Any] = {}

    def with_source_task(self, task: Task) -> "RelationshipBuilder":
        if not isinstance(task, Task):
            raise InvalidTaskRelationshipError(
                f"source_task must be a Task instance, got {task!r}."
            )
        self._source_task = task
        return self

    def with_target_task(self, task: Task) -> "RelationshipBuilder":
        if not isinstance(task, Task):
            raise InvalidTaskRelationshipError(
                f"target_task must be a Task instance, got {task!r}."
            )
        self._target_task = task
        return self

    def with_type(self, relationship_type: RelationshipType) -> "RelationshipBuilder":
        if not isinstance(relationship_type, RelationshipType):
            raise InvalidTaskRelationshipError(
                f"relationship_type must be a RelationshipType instance, "
                f"got {relationship_type!r}."
            )
        self._relationship_type = relationship_type
        return self

    def with_metadata(self, key: str, value: Any) -> "RelationshipBuilder":
        validated_key = _require_non_empty_string(key, label="metadata key")
        self._metadata_extra[validated_key] = value
        return self

    def build(self) -> TaskRelationship:
        return TaskRelationship(
            source_task=self._source_task,
            target_task=self._target_task,
            relationship_type=self._relationship_type,
            metadata=RelationshipMetadata(extra=dict(self._metadata_extra)),
        )
