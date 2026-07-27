"""
The GoalMetadata value object for the ArgusOS Goal Framework.

Purpose:
    Hold lightweight, descriptive bookkeeping about a single Goal
    instance itself - when it was created, what schema version
    produced it, a correlation identifier for tracing it, who owns it,
    and what tags organize it - per
    factory/packages/038_GOAL_FRAMEWORK.md. "Follow the existing
    metadata conventions established by Project and Workspace."
    GoalMetadata is pure data: it does not compute anything and knows
    nothing about what a Goal actually represents.

Field Order - Following ProjectMetadata/WorkspaceMetadata's Own
Precedent, Not This Package's Own Literal Listed Order:
    This package's own literal field list reads "created_at, owner,
    correlation_id, version, tags, extra" - the identical literal
    order Package 037's own work order used for WorkspaceMetadata,
    resolved there in favor of ProjectMetadata's own established order
    instead. This package's own explicit governing instruction -
    "Follow the existing metadata conventions established by Project
    and Workspace" - names that precedent directly, by name, for the
    first time in this codebase's history (every prior "follow
    existing conventions" instruction referred to the convention in
    the abstract, never citing specific prior packages by name). There
    is therefore no genuine tension to resolve here at all: this
    module's own declared order is `created_at`, `version`,
    `correlation_id`, `owner`, `tags`, `extra` - ProjectMetadata's
    (036) and WorkspaceMetadata's (037) own identical order, followed
    a third time.

owner/tags Are System-Managed Fields, Not Builder-Overridable - See
builder.py:
    Mirrors ProjectMetadata's (036) / WorkspaceMetadata's (037) own
    identical precedent: GoalBuilder's own Responsibilities list names
    exactly "assign name, assign description, assign status, assign
    priority, assign metadata" - one bullet for "assign metadata," not
    separate bullets for "assign owner"/"assign tags." `owner` and
    `tags` therefore join `created_at`/`version`/`correlation_id` as
    fields GoalBuilder does not expose a dedicated setter for - they
    remain at their own defaults (`None`, an empty tuple) for every
    Goal built via the supported GoalBuilder path in Version 1,
    settable only through `with_metadata()`'s own `extra` mapping or
    by constructing GoalMetadata directly. See builder.py's own module
    docstring for the complete reasoning.

Mirrors ContextMetadata/PlanningMetadata/TraceMetadata/TaskMetadata/
RelationshipMetadata/ExecutionMetadata/CapabilityMetadata/
CapabilityExecutionMetadata/CapabilityContextMetadata/ProjectMetadata/
WorkspaceMetadata's Shape For Its Own Shared Fields:
    `created_at`, `version`, `correlation_id`, and `extra` are typed
    and defaulted identically to every sibling metadata module -
    `created_at` defaults to the current UTC time, `version` defaults
    to this module's own `GOAL_METADATA_VERSION`, `correlation_id`
    defaults to a fresh uuid4 string, and `extra` is wrapped in
    `MappingProxyType` with a defensive copy in `__post_init__`,
    exactly as every prior metadata module already does.

tags Is Wrapped In A Tuple, Mirroring ProjectMetadata/WorkspaceMetadata's
Own Identical Convention:
    `tags` defaults to an empty tuple and is coerced to a tuple in
    `__post_init__` regardless of what sequence type is given.

Responsibilities:
    - GoalMetadata: hold a Goal's own creation timestamp, schema
      version, correlation identifier, owner, tags, and any
      caller-supplied extra data as an immutable value object.

Non-Responsibilities:
    - GoalMetadata performs no computation and holds no runtime state
      - not a snapshot of any live service, not a cache.
    - GoalMetadata performs no validation of its own fields beyond the
      standard `extra`/`tags` wrapping in `__post_init__` - see
      builder.py's own module docstring for where malformed input to
      the *builder's* own `with_metadata()` is rejected.

Dependencies:
    None beyond the standard library.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Optional, Sequence

GOAL_METADATA_VERSION = "1.0"


@dataclass(frozen=True)
class GoalMetadata:
    """
    Immutable, descriptive bookkeeping about a single Goal. See the
    module docstring for the full field semantics and for why this
    module's own declared order follows ProjectMetadata's/
    WorkspaceMetadata's own established precedent rather than this
    package's own literal listed order.

    Fields:
        created_at: When this GoalMetadata (and, in practice, the Goal
            it describes) was created. Defaults to the current UTC
            time.
        version: The schema version of this metadata shape. Defaults
            to GOAL_METADATA_VERSION.
        correlation_id: An opaque identifier for tracing this Goal's
            own metadata across the system. Defaults to a fresh uuid4
            string.
        owner: A human-readable identifier for who owns this Goal.
            Defaults to None. Not settable via GoalBuilder in Version
            1 - see the module docstring.
        tags: Free-form labels organizing this Goal. Defaults to an
            empty tuple. Always stored as a tuple, regardless of what
            sequence type is given. Not settable via GoalBuilder in
            Version 1 - see the module docstring.
        extra: Caller-supplied key/value data, populated exclusively
            through GoalBuilder.with_metadata(). Defaults to an empty
            mapping, wrapped in MappingProxyType.
    """

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = GOAL_METADATA_VERSION
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    owner: Optional[str] = None
    tags: Sequence[str] = field(default_factory=tuple)
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "tags", tuple(self.tags))
        object.__setattr__(self, "extra", MappingProxyType(dict(self.extra)))
