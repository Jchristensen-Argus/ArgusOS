"""
The ProjectBuilder for the ArgusOS Project Framework.

Purpose:
    Provide a mutable, fluent way to assemble a Project's fields one
    at a time before producing a single immutable Project snapshot,
    per factory/packages/036_PROJECT_FRAMEWORK.md. "Builder is the
    only mutable object." Directly mirrors argus.task.builder.
    TaskBuilder (029) - the same fluent-builder pattern applied to the
    Project Framework, minus the `relationships` trio Task gained in
    Package 031, since this package introduces no ownership
    relationships yet (see project.py's own "Future Relationship"
    note).

Responsibilities Beyond The Work Order's Own Four-Item List:
    This package's own "Responsibilities" list for ProjectBuilder
    names exactly four items: "assign name, assign description,
    assign status, build immutable Project" plus "assign metadata" as
    a fifth - it does not separately name "assign owner"/"assign
    tags" as their own bullets, even though this package's own
    ProjectMetadata "Suggested fields" list names both. Read "assign
    metadata" as covering only the `extra` mapping - the same reading
    TaskBuilder's own `with_metadata()` already established for
    TaskMetadata's identical `extra` field - not as license to expose
    a setter for every field ProjectMetadata happens to hold.
    `with_name()`, `with_description()`, `with_status()`, and
    `with_metadata()` are the complete method surface; no
    `with_owner()`/`with_tags()` exists. See metadata.py's own module
    docstring for the complete reasoning.

with_name() / with_description() / with_status() Are Singular Fields,
Overwritten, Not Accumulated:
    Each of `name`, `description`, and `status` is a single scalar
    field on `Project`, not a collection - calling `with_name()` (or
    `with_description()`/`with_status()`) more than once simply
    overwrites the previous value, the last call before build() wins.
    This mirrors TaskBuilder.with_name()/with_description()/
    with_status()'s own identical "singular field is overwritten"
    rule.

with_metadata() Only Ever Populates `extra`:
    ProjectMetadata's `created_at`, `version`, `correlation_id`,
    `owner`, and `tags` fields are all system-managed - not settable
    through ProjectBuilder in Version 1 (see metadata.py's own module
    docstring for `owner`/`tags` specifically, and TaskMetadata's own
    precedent for `created_at`/`version`/`correlation_id`).
    `with_metadata(key, value)` adds one key/value pair to the
    eventual `ProjectMetadata.extra` mapping; calling it multiple
    times with different keys accumulates, and calling it twice with
    the same key overwrites that key's value - the last call wins,
    mirroring TaskBuilder/ContextBuilder/PlanningSessionBuilder/
    TraceBuilder's identical rule. A caller wanting a specific
    `owner`/`tags` value in Version 1 must either populate it through
    `extra` (for example, `with_metadata("owner", "Jane")`) or
    construct `ProjectMetadata` directly, bypassing the builder.

No with_project_id():
    This package's own Responsibilities list does not name "assign
    id" - continuing the "no with_<id>() unless explicitly named"
    precedent already established by RelationshipBuilder (031),
    ExecutionResultBuilder (032), CapabilityExecutionResultBuilder
    (034), and CapabilityContextBuilder (035). `project_id` is left at
    its own fresh-uuid4 default for every Project this builder
    produces.

Validation Lives Here, Not On Project:
    See project.py's own module docstring - Project performs no
    validation of its own; every `with_*` method below validates its
    argument before assigning it, raising InvalidProjectError for
    malformed input. build() itself performs no additional validation
    - by the time build() runs, every assigned value has already been
    validated at the point it was set.

Independent Snapshots:
    build() constructs a fresh Project (and a fresh ProjectMetadata)
    from this builder's current accumulated state every time it is
    called. Continuing to call `with_*` methods on the same builder
    after calling build() - or calling build() more than once - never
    mutates a Project already returned by an earlier build() call,
    since Project itself is immutable and each build() call
    constructs a fresh instance.

Responsibilities:
    - ProjectBuilder: assign a Project's `name`, `description`,
      `status`, and `extra` metadata, with per-field validation, and
      produce an immutable Project snapshot on build().

Non-Responsibilities:
    - ProjectBuilder performs no reasoning, scheduling, dispatch, or
      execution of any kind - it only validates and assigns plain
      data.
    - ProjectBuilder is not a service - see interfaces.py's own module
      docstring.

Dependencies:
    argus.project.project (Project), argus.project.status
    (ProjectStatus), argus.project.metadata (ProjectMetadata),
    argus.project.exceptions (InvalidProjectError), argus.project.interfaces
    (IProjectBuilder).
"""

from typing import Any, Dict

from argus.project.exceptions import InvalidProjectError
from argus.project.interfaces import IProjectBuilder
from argus.project.metadata import ProjectMetadata
from argus.project.project import Project
from argus.project.status import ProjectStatus


def _require_non_empty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidProjectError(f"{label} must be a non-empty string, got {value!r}.")
    return value


class ProjectBuilder(IProjectBuilder):
    """
    A mutable, fluent builder for Project. See the module docstring
    for the full assignment and validation semantics.
    """

    def __init__(self) -> None:
        self._name: str = ""
        self._description: str = ""
        self._status: ProjectStatus = ProjectStatus.PLANNING
        self._metadata_extra: Dict[str, Any] = {}

    def with_name(self, name: str) -> "ProjectBuilder":
        self._name = _require_non_empty_string(name, label="name")
        return self

    def with_description(self, description: str) -> "ProjectBuilder":
        if not isinstance(description, str):
            raise InvalidProjectError(
                f"description must be a string, got {description!r}."
            )
        self._description = description
        return self

    def with_status(self, status: ProjectStatus) -> "ProjectBuilder":
        if not isinstance(status, ProjectStatus):
            raise InvalidProjectError(
                f"status must be a ProjectStatus instance, got {status!r}."
            )
        self._status = status
        return self

    def with_metadata(self, key: str, value: Any) -> "ProjectBuilder":
        validated_key = _require_non_empty_string(key, label="metadata key")
        self._metadata_extra[validated_key] = value
        return self

    def build(self) -> Project:
        return Project(
            name=self._name,
            description=self._description,
            status=self._status,
            metadata=ProjectMetadata(extra=dict(self._metadata_extra)),
        )
