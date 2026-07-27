"""
The GoalBuilder for the ArgusOS Goal Framework.

Purpose:
    Provide a mutable, fluent way to assemble a Goal's fields one at a
    time before producing a single immutable Goal snapshot, per
    factory/packages/038_GOAL_FRAMEWORK.md. "Builder is the only
    mutable object." Directly mirrors argus.project.builder.
    ProjectBuilder (036) / argus.workspace.builder.WorkspaceBuilder
    (037), with one genuine addition: with_priority().

with_priority() Is Explicitly Named, Unlike with_owner()/with_tags():
    This package's own "Responsibilities" list for GoalBuilder names
    exactly five items plus build: "assign name, assign description,
    assign status, assign priority, assign metadata, build immutable
    Goal." Unlike `owner`/`tags` on GoalMetadata (deliberately left
    without a dedicated builder method - see metadata.py's own module
    docstring), `priority` is a top-level field on Goal itself, not a
    metadata sub-field, and this package's own Responsibilities list
    names "assign priority" as its own explicit bullet, exactly the
    way "assign status" is its own bullet. `with_priority()` is
    therefore implemented as a full, validated, singular-field setter
    - the same shape as `with_status()` - not folded into
    `with_metadata()`'s own extra-only behavior.

Responsibilities Beyond The Work Order's Own Five-Item List:
    Read "assign metadata" as covering only the `extra` mapping - the
    same reading ProjectBuilder's/WorkspaceBuilder's own
    `with_metadata()` already established for their own identical
    `extra` field (036, 037). `with_name()`, `with_description()`,
    `with_status()`, `with_priority()`, and `with_metadata()` are the
    complete method surface; no `with_owner()`/`with_tags()` exists.
    See metadata.py's own module docstring for the complete reasoning.

with_name() / with_description() / with_status() / with_priority()
Are Singular Fields, Overwritten, Not Accumulated:
    Each of `name`, `description`, `status`, and `priority` is a
    single scalar field on `Goal`, not a collection - calling any of
    these more than once simply overwrites the previous value, the
    last call before build() wins. This mirrors ProjectBuilder's/
    WorkspaceBuilder's own identical "singular field is overwritten"
    rule, extended to the new `priority` field.

with_metadata() Only Ever Populates `extra`:
    GoalMetadata's `created_at`, `version`, `correlation_id`, `owner`,
    and `tags` fields are all system-managed - not settable through
    GoalBuilder in Version 1 (see metadata.py's own module docstring).
    `with_metadata(key, value)` adds one key/value pair to the
    eventual `GoalMetadata.extra` mapping; calling it multiple times
    with different keys accumulates, and calling it twice with the
    same key overwrites that key's value - the last call wins.

No with_goal_id():
    This package's own Responsibilities list does not name "assign
    id" - continuing the "no with_<id>() unless explicitly named"
    precedent already established by RelationshipBuilder (031),
    ExecutionResultBuilder (032), CapabilityExecutionResultBuilder
    (034), CapabilityContextBuilder (035), ProjectBuilder (036), and
    WorkspaceBuilder (037). `goal_id` is left at its own fresh-uuid4
    default for every Goal this builder produces.

Validation Lives Here, Not On Goal:
    See goal.py's own module docstring - Goal performs no validation
    of its own; every `with_*` method below validates its argument
    before assigning it, raising InvalidGoalError for malformed input.
    build() itself performs no additional validation - by the time
    build() runs, every assigned value has already been validated at
    the point it was set.

Independent Snapshots:
    build() constructs a fresh Goal (and a fresh GoalMetadata) from
    this builder's current accumulated state every time it is called.
    Continuing to call `with_*` methods on the same builder after
    calling build() - or calling build() more than once - never
    mutates a Goal already returned by an earlier build() call, since
    Goal itself is immutable and each build() call constructs a fresh
    instance.

Responsibilities:
    - GoalBuilder: assign a Goal's `name`, `description`, `status`,
      `priority`, and `extra` metadata, with per-field validation, and
      produce an immutable Goal snapshot on build().

Non-Responsibilities:
    - GoalBuilder performs no reasoning, scheduling, dispatch, or
      execution of any kind - it only validates and assigns plain
      data.
    - GoalBuilder is not a service - see interfaces.py's own module
      docstring.

Dependencies:
    argus.goal.goal (Goal), argus.goal.status (GoalStatus),
    argus.goal.priority (GoalPriority), argus.goal.metadata
    (GoalMetadata), argus.goal.exceptions (InvalidGoalError),
    argus.goal.interfaces (IGoalBuilder).
"""

from typing import Any, Dict

from argus.goal.exceptions import InvalidGoalError
from argus.goal.goal import Goal
from argus.goal.interfaces import IGoalBuilder
from argus.goal.metadata import GoalMetadata
from argus.goal.priority import GoalPriority
from argus.goal.status import GoalStatus


def _require_non_empty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidGoalError(f"{label} must be a non-empty string, got {value!r}.")
    return value


class GoalBuilder(IGoalBuilder):
    """
    A mutable, fluent builder for Goal. See the module docstring for
    the full assignment and validation semantics.
    """

    def __init__(self) -> None:
        self._name: str = ""
        self._description: str = ""
        self._status: GoalStatus = GoalStatus.PLANNING
        self._priority: GoalPriority = GoalPriority.NORMAL
        self._metadata_extra: Dict[str, Any] = {}

    def with_name(self, name: str) -> "GoalBuilder":
        self._name = _require_non_empty_string(name, label="name")
        return self

    def with_description(self, description: str) -> "GoalBuilder":
        if not isinstance(description, str):
            raise InvalidGoalError(
                f"description must be a string, got {description!r}."
            )
        self._description = description
        return self

    def with_status(self, status: GoalStatus) -> "GoalBuilder":
        if not isinstance(status, GoalStatus):
            raise InvalidGoalError(
                f"status must be a GoalStatus instance, got {status!r}."
            )
        self._status = status
        return self

    def with_priority(self, priority: GoalPriority) -> "GoalBuilder":
        if not isinstance(priority, GoalPriority):
            raise InvalidGoalError(
                f"priority must be a GoalPriority instance, got {priority!r}."
            )
        self._priority = priority
        return self

    def with_metadata(self, key: str, value: Any) -> "GoalBuilder":
        validated_key = _require_non_empty_string(key, label="metadata key")
        self._metadata_extra[validated_key] = value
        return self

    def build(self) -> Goal:
        return Goal(
            name=self._name,
            description=self._description,
            status=self._status,
            priority=self._priority,
            metadata=GoalMetadata(extra=dict(self._metadata_extra)),
        )
