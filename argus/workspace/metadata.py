"""
The WorkspaceMetadata value object for the ArgusOS Workspace
Framework.

Purpose:
    Hold lightweight, descriptive bookkeeping about a single Workspace
    instance itself - when it was created, what schema version
    produced it, a correlation identifier for tracing it, who owns it,
    and what tags organize it - per
    factory/packages/037_WORKSPACE_FRAMEWORK.md. "Follow the metadata
    conventions established throughout ArgusOS." WorkspaceMetadata is
    pure data: it does not compute anything and knows nothing about
    what a Workspace actually contains.

Field Order - Following ProjectMetadata's Own Precedent (036), Not
This Package's Own Literal Listed Order:
    This package's own literal field list reads "created_at, owner,
    correlation_id, version, tags, extra." Unlike Package 036's own
    "Suggested fields" header, this package uses the same imperative
    "Fields:" header every metadata module's work order has used since
    Package 028 - but its own explicit governing instruction is
    "Follow the metadata conventions established throughout ArgusOS,"
    the identical phrase (and identical role) every prior metadata
    module's own "follow existing conventions" instruction has played
    since 028, each time settling a field-*order* tension in favor of
    the codebase's own established order over the work order's own
    literal listed order. What makes this package different is what
    "established... throughout ArgusOS" now includes: Package 036
    (`ProjectMetadata`) already resolved the *composition* question -
    keeping the pre-existing `created_at`/`version`/`correlation_id`
    quartet's own relative order and appending `owner`/`tags` before
    `extra` - for the first metadata module ever suggested with its
    own domain-specific fields. This package's own field set is
    identical to `ProjectMetadata`'s (the same six fields, no more, no
    fewer), so "follow existing conventions" now has a direct, literal
    precedent to follow, not just the older four-field quartet.
    Declared order: `created_at`, `version`, `correlation_id`,
    `owner`, `tags`, `extra` - `ProjectMetadata`'s own order, exactly.

owner/tags Are System-Managed Fields, Not Builder-Overridable - See
builder.py:
    Mirrors ProjectMetadata's own identical precedent (036), itself an
    extension of TaskMetadata's own "created_at/version/correlation_id
    are system-assigned; only extra is caller-populated" rule (029):
    WorkspaceBuilder's own Responsibilities list names exactly "assign
    name, assign description, assign status, assign metadata" - one
    bullet for "assign metadata," not separate bullets for "assign
    owner"/"assign tags." `owner` and `tags` therefore join
    `created_at`/`version`/`correlation_id` as fields WorkspaceBuilder
    does not expose a dedicated setter for - they remain at their own
    defaults (`None`, an empty tuple) for every Workspace built via the
    supported WorkspaceBuilder path in Version 1, settable only
    through `with_metadata()`'s own `extra` mapping or by constructing
    WorkspaceMetadata directly. See builder.py's own module docstring
    for the complete reasoning, and this package's own Known
    Limitations for the fuller statement.

Mirrors ContextMetadata/PlanningMetadata/TraceMetadata/TaskMetadata/
RelationshipMetadata/ExecutionMetadata/CapabilityMetadata/
CapabilityExecutionMetadata/CapabilityContextMetadata/ProjectMetadata's
Shape For Its Own Shared Fields:
    `created_at`, `version`, `correlation_id`, and `extra` are typed
    and defaulted identically to every sibling metadata module -
    `created_at` defaults to the current UTC time, `version` defaults
    to this module's own `WORKSPACE_METADATA_VERSION`,
    `correlation_id` defaults to a fresh uuid4 string, and `extra` is
    wrapped in `MappingProxyType` with a defensive copy in
    `__post_init__`, exactly as every prior metadata module already
    does.

tags Is Wrapped In A Tuple, Mirroring ProjectMetadata's Own Identical
Convention:
    `tags` defaults to an empty tuple and is coerced to a tuple in
    `__post_init__` regardless of what sequence type is given,
    mirroring `ProjectMetadata.tags` (036)/`Task.relationships`
    (031)/`Plan.tasks` (030)'s own "always stored as a tuple"
    convention for ordered collection fields.

Responsibilities:
    - WorkspaceMetadata: hold a Workspace's own creation timestamp,
      schema version, correlation identifier, owner, tags, and any
      caller-supplied extra data as an immutable value object.

Non-Responsibilities:
    - WorkspaceMetadata performs no computation and holds no runtime
      state - not a snapshot of any live service, not a cache.
    - WorkspaceMetadata performs no validation of its own fields
      beyond the standard `extra`/`tags` wrapping in `__post_init__` -
      see builder.py's own module docstring for where malformed input
      to the *builder's* own `with_metadata()` is rejected.

Dependencies:
    None beyond the standard library.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Optional, Sequence

WORKSPACE_METADATA_VERSION = "1.0"


@dataclass(frozen=True)
class WorkspaceMetadata:
    """
    Immutable, descriptive bookkeeping about a single Workspace. See
    the module docstring for the full field semantics and for why
    this module's own declared order follows ProjectMetadata's own
    established precedent rather than this package's own literal
    listed order.

    Fields:
        created_at: When this WorkspaceMetadata (and, in practice, the
            Workspace it describes) was created. Defaults to the
            current UTC time.
        version: The schema version of this metadata shape. Defaults
            to WORKSPACE_METADATA_VERSION.
        correlation_id: An opaque identifier for tracing this
            Workspace's own metadata across the system. Defaults to a
            fresh uuid4 string.
        owner: A human-readable identifier for who owns this
            Workspace. Defaults to None. Not settable via
            WorkspaceBuilder in Version 1 - see the module docstring.
        tags: Free-form labels organizing this Workspace. Defaults to
            an empty tuple. Always stored as a tuple, regardless of
            what sequence type is given. Not settable via
            WorkspaceBuilder in Version 1 - see the module docstring.
        extra: Caller-supplied key/value data, populated exclusively
            through WorkspaceBuilder.with_metadata(). Defaults to an
            empty mapping, wrapped in MappingProxyType.
    """

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = WORKSPACE_METADATA_VERSION
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    owner: Optional[str] = None
    tags: Sequence[str] = field(default_factory=tuple)
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "tags", tuple(self.tags))
        object.__setattr__(self, "extra", MappingProxyType(dict(self.extra)))
