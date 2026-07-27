"""
The WorkspaceBuilder for the ArgusOS Workspace Framework.

Purpose:
    Provide a mutable, fluent way to assemble a Workspace's fields one
    at a time before producing a single immutable Workspace snapshot,
    per factory/packages/037_WORKSPACE_FRAMEWORK.md. "Builder is the
    only mutable object." Directly mirrors argus.project.builder.
    ProjectBuilder (036) - the same fluent-builder pattern applied one
    level up the ownership hierarchy.

Responsibilities Beyond The Work Order's Own Four-Item List:
    This package's own "Responsibilities" list for WorkspaceBuilder
    names exactly four items plus "assign metadata" as a fifth -
    "assign name, assign description, assign status, assign metadata,
    build immutable Workspace" - it does not separately name "assign
    owner"/"assign tags" as their own bullets, even though this
    package's own WorkspaceMetadata Fields list names both. Read
    "assign metadata" as covering only the `extra` mapping - the same
    reading ProjectBuilder's own `with_metadata()` already established
    for ProjectMetadata's identical `extra` field (036), itself
    following TaskBuilder's own precedent (029). `with_name()`,
    `with_description()`, `with_status()`, and `with_metadata()` are
    the complete method surface; no `with_owner()`/`with_tags()`
    exists. See metadata.py's own module docstring for the complete
    reasoning.

with_name() / with_description() / with_status() Are Singular Fields,
Overwritten, Not Accumulated:
    Each of `name`, `description`, and `status` is a single scalar
    field on `Workspace`, not a collection - calling `with_name()` (or
    `with_description()`/`with_status()`) more than once simply
    overwrites the previous value, the last call before build() wins.
    This mirrors ProjectBuilder.with_name()/with_description()/
    with_status()'s own identical "singular field is overwritten"
    rule.

with_metadata() Only Ever Populates `extra`:
    WorkspaceMetadata's `created_at`, `version`, `correlation_id`,
    `owner`, and `tags` fields are all system-managed - not settable
    through WorkspaceBuilder in Version 1 (see metadata.py's own
    module docstring). `with_metadata(key, value)` adds one key/value
    pair to the eventual `WorkspaceMetadata.extra` mapping; calling it
    multiple times with different keys accumulates, and calling it
    twice with the same key overwrites that key's value - the last
    call wins, mirroring ProjectBuilder/TaskBuilder/ContextBuilder/
    PlanningSessionBuilder/TraceBuilder's identical rule. A caller
    wanting a specific `owner`/`tags` value in Version 1 must either
    populate it through `extra` (for example, `with_metadata("owner",
    "Joel Christensen")`) or construct `WorkspaceMetadata` directly,
    bypassing the builder.

No with_workspace_id():
    This package's own Responsibilities list does not name "assign
    id" - continuing the "no with_<id>() unless explicitly named"
    precedent already established by RelationshipBuilder (031),
    ExecutionResultBuilder (032), CapabilityExecutionResultBuilder
    (034), CapabilityContextBuilder (035), and ProjectBuilder (036).
    `workspace_id` is left at its own fresh-uuid4 default for every
    Workspace this builder produces.

Validation Lives Here, Not On Workspace:
    See workspace.py's own module docstring - Workspace performs no
    validation of its own; every `with_*` method below validates its
    argument before assigning it, raising InvalidWorkspaceError for
    malformed input. build() itself performs no additional validation
    - by the time build() runs, every assigned value has already been
    validated at the point it was set.

Independent Snapshots:
    build() constructs a fresh Workspace (and a fresh
    WorkspaceMetadata) from this builder's current accumulated state
    every time it is called. Continuing to call `with_*` methods on
    the same builder after calling build() - or calling build() more
    than once - never mutates a Workspace already returned by an
    earlier build() call, since Workspace itself is immutable and each
    build() call constructs a fresh instance.

Responsibilities:
    - WorkspaceBuilder: assign a Workspace's `name`, `description`,
      `status`, and `extra` metadata, with per-field validation, and
      produce an immutable Workspace snapshot on build().

Non-Responsibilities:
    - WorkspaceBuilder performs no reasoning, scheduling, dispatch, or
      execution of any kind - it only validates and assigns plain
      data.
    - WorkspaceBuilder is not a service - see interfaces.py's own
      module docstring.

Dependencies:
    argus.workspace.workspace (Workspace), argus.workspace.status
    (WorkspaceStatus), argus.workspace.metadata (WorkspaceMetadata),
    argus.workspace.exceptions (InvalidWorkspaceError),
    argus.workspace.interfaces (IWorkspaceBuilder).
"""

from typing import Any, Dict

from argus.workspace.exceptions import InvalidWorkspaceError
from argus.workspace.interfaces import IWorkspaceBuilder
from argus.workspace.metadata import WorkspaceMetadata
from argus.workspace.status import WorkspaceStatus
from argus.workspace.workspace import Workspace


def _require_non_empty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidWorkspaceError(
            f"{label} must be a non-empty string, got {value!r}."
        )
    return value


class WorkspaceBuilder(IWorkspaceBuilder):
    """
    A mutable, fluent builder for Workspace. See the module docstring
    for the full assignment and validation semantics.
    """

    def __init__(self) -> None:
        self._name: str = ""
        self._description: str = ""
        self._status: WorkspaceStatus = WorkspaceStatus.ACTIVE
        self._metadata_extra: Dict[str, Any] = {}

    def with_name(self, name: str) -> "WorkspaceBuilder":
        self._name = _require_non_empty_string(name, label="name")
        return self

    def with_description(self, description: str) -> "WorkspaceBuilder":
        if not isinstance(description, str):
            raise InvalidWorkspaceError(
                f"description must be a string, got {description!r}."
            )
        self._description = description
        return self

    def with_status(self, status: WorkspaceStatus) -> "WorkspaceBuilder":
        if not isinstance(status, WorkspaceStatus):
            raise InvalidWorkspaceError(
                f"status must be a WorkspaceStatus instance, got {status!r}."
            )
        self._status = status
        return self

    def with_metadata(self, key: str, value: Any) -> "WorkspaceBuilder":
        validated_key = _require_non_empty_string(key, label="metadata key")
        self._metadata_extra[validated_key] = value
        return self

    def build(self) -> Workspace:
        return Workspace(
            name=self._name,
            description=self._description,
            status=self._status,
            metadata=WorkspaceMetadata(extra=dict(self._metadata_extra)),
        )
