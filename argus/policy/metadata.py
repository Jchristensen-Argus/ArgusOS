"""
The PolicyMetadata value object for the ArgusOS Policy Framework.

Purpose:
    Hold lightweight, descriptive bookkeeping about a single Policy
    instance itself - when it was created, what schema version
    produced it, a correlation identifier for tracing it, who owns it,
    and what tags organize it - per
    factory/packages/040_POLICY_FRAMEWORK.md. "Follow the metadata
    conventions established by Project, Workspace, Goal, and
    DecisionRecord." PolicyMetadata is pure data: it does not compute
    anything and knows nothing about what a Policy actually governs.

Field Order - Following ProjectMetadata/WorkspaceMetadata/GoalMetadata/
DecisionRecordMetadata's Own Precedent, Not This Package's Own Literal
Listed Order:
    This package's own literal field list reads "created_at, owner,
    correlation_id, version, tags, extra" - the identical literal
    order every prior organizational-tier metadata module's own work
    order has used, each resolved in favor of ProjectMetadata's own
    established order instead. This package's own explicit governing
    instruction - "Follow the metadata conventions established by
    Project, Workspace, Goal, and DecisionRecord" - names that
    precedent directly, by name, for a fourth time (037, 038, and 039
    each did the same). There is therefore no genuine tension to
    resolve here: this module's own declared order is `created_at`,
    `version`, `correlation_id`, `owner`, `tags`, `extra` -
    ProjectMetadata's (036), WorkspaceMetadata's (037), GoalMetadata's
    (038), and DecisionRecordMetadata's (039) own identical order,
    followed a fifth time.

owner/tags Are System-Managed Fields, Not Builder-Overridable - See
builder.py:
    Mirrors every sibling metadata module's own identical precedent:
    PolicyBuilder's own Responsibilities list names exactly "assign
    name, assign description, assign status, assign scope, assign
    metadata" - one bullet for "assign metadata," not separate
    bullets for "assign owner"/"assign tags." `owner` and `tags`
    therefore join `created_at`/`version`/`correlation_id` as fields
    PolicyBuilder does not expose a dedicated setter for.

Responsibilities:
    - PolicyMetadata: hold a Policy's own creation timestamp, schema
      version, correlation identifier, owner, tags, and any
      caller-supplied extra data as an immutable value object.

Non-Responsibilities:
    - PolicyMetadata performs no computation and holds no runtime
      state.
    - PolicyMetadata performs no validation of its own fields beyond
      the standard `extra`/`tags` wrapping in `__post_init__`.

Dependencies:
    None beyond the standard library.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Optional, Sequence

POLICY_METADATA_VERSION = "1.0"


@dataclass(frozen=True)
class PolicyMetadata:
    """
    Immutable, descriptive bookkeeping about a single Policy. See the
    module docstring for the full field semantics and for why this
    module's own declared order follows ProjectMetadata's /
    WorkspaceMetadata's / GoalMetadata's / DecisionRecordMetadata's
    own established precedent rather than this package's own literal
    listed order.

    Fields:
        created_at: When this PolicyMetadata (and, in practice, the
            Policy it describes) was created. Defaults to the current
            UTC time.
        version: The schema version of this metadata shape. Defaults
            to POLICY_METADATA_VERSION.
        correlation_id: An opaque identifier for tracing this Policy's
            own metadata across the system. Defaults to a fresh uuid4
            string.
        owner: A human-readable identifier for who owns this Policy.
            Defaults to None. Not settable via PolicyBuilder in
            Version 1 - see the module docstring.
        tags: Free-form labels organizing this Policy. Defaults to an
            empty tuple. Always stored as a tuple, regardless of what
            sequence type is given. Not settable via PolicyBuilder in
            Version 1 - see the module docstring.
        extra: Caller-supplied key/value data, populated exclusively
            through PolicyBuilder.with_metadata(). Defaults to an
            empty mapping, wrapped in MappingProxyType.
    """

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = POLICY_METADATA_VERSION
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    owner: Optional[str] = None
    tags: Sequence[str] = field(default_factory=tuple)
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "tags", tuple(self.tags))
        object.__setattr__(self, "extra", MappingProxyType(dict(self.extra)))
