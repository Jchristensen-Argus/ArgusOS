"""
The DecisionRecordMetadata value object for the ArgusOS Decision
Framework.

Purpose:
    Hold lightweight, descriptive bookkeeping about a single
    DecisionRecord instance itself - when it was created, what schema
    version produced it, a correlation identifier for tracing it, who
    owns it, and what tags organize it - per
    factory/packages/039_DECISION_FRAMEWORK.md. "Follow the metadata
    conventions established by Project, Workspace, and Goal."
    DecisionRecordMetadata is pure data: it does not compute anything
    and knows nothing about what a DecisionRecord actually represents.

Naming Note - DecisionRecordMetadata, Not DecisionMetadata:
    See status.py's own module docstring for the full reasoning: this
    package's own model is named DecisionRecord throughout, to avoid
    colliding with Package 021's own pre-existing, unrelated Decision
    Engine concept. There is no pre-existing DecisionMetadata to
    collide with, but the name is kept consistent with
    DecisionRecord/DecisionRecordStatus/DecisionRecordPriority/
    DecisionRecordBuilder for readability.

Field Order - Following ProjectMetadata/WorkspaceMetadata/GoalMetadata's
Own Precedent, Not This Package's Own Literal Listed Order:
    This package's own literal field list reads "created_at, owner,
    correlation_id, version, tags, extra" - the identical literal
    order Packages 037's and 038's own work orders each used, both
    resolved in favor of ProjectMetadata's own established order
    instead. This package's own explicit governing instruction -
    "Follow the metadata conventions established by Project,
    Workspace, and Goal" - names that precedent directly, by name,
    exactly as Package 038's own instruction did. There is therefore
    no genuine tension to resolve here at all: this module's own
    declared order is `created_at`, `version`, `correlation_id`,
    `owner`, `tags`, `extra` - ProjectMetadata's (036),
    WorkspaceMetadata's (037), and GoalMetadata's (038) own identical
    order, followed a fourth time.

owner/tags Are System-Managed Fields, Not Builder-Overridable - See
builder.py:
    Mirrors ProjectMetadata's (036) / WorkspaceMetadata's (037) /
    GoalMetadata's (038) own identical precedent:
    DecisionRecordBuilder's own Responsibilities list names exactly
    "assign title, assign question, assign status, assign priority,
    assign metadata" - one bullet for "assign metadata," not separate
    bullets for "assign owner"/"assign tags." `owner` and `tags`
    therefore join `created_at`/`version`/`correlation_id` as fields
    DecisionRecordBuilder does not expose a dedicated setter for -
    they remain at their own defaults (`None`, an empty tuple) for
    every DecisionRecord built via the supported DecisionRecordBuilder
    path in Version 1, settable only through `with_metadata()`'s own
    `extra` mapping or by constructing DecisionRecordMetadata
    directly.

Responsibilities:
    - DecisionRecordMetadata: hold a DecisionRecord's own creation
      timestamp, schema version, correlation identifier, owner, tags,
      and any caller-supplied extra data as an immutable value object.

Non-Responsibilities:
    - DecisionRecordMetadata performs no computation and holds no
      runtime state.
    - DecisionRecordMetadata performs no validation of its own fields
      beyond the standard `extra`/`tags` wrapping in `__post_init__`.

Dependencies:
    None beyond the standard library.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Optional, Sequence

DECISION_RECORD_METADATA_VERSION = "1.0"


@dataclass(frozen=True)
class DecisionRecordMetadata:
    """
    Immutable, descriptive bookkeeping about a single DecisionRecord.
    See the module docstring for the full field semantics and for why
    this module's own declared order follows ProjectMetadata's /
    WorkspaceMetadata's / GoalMetadata's own established precedent
    rather than this package's own literal listed order.

    Fields:
        created_at: When this DecisionRecordMetadata (and, in
            practice, the DecisionRecord it describes) was created.
            Defaults to the current UTC time.
        version: The schema version of this metadata shape. Defaults
            to DECISION_RECORD_METADATA_VERSION.
        correlation_id: An opaque identifier for tracing this
            DecisionRecord's own metadata across the system. Defaults
            to a fresh uuid4 string.
        owner: A human-readable identifier for who owns this
            DecisionRecord. Defaults to None. Not settable via
            DecisionRecordBuilder in Version 1 - see the module
            docstring.
        tags: Free-form labels organizing this DecisionRecord.
            Defaults to an empty tuple. Always stored as a tuple,
            regardless of what sequence type is given. Not settable
            via DecisionRecordBuilder in Version 1 - see the module
            docstring.
        extra: Caller-supplied key/value data, populated exclusively
            through DecisionRecordBuilder.with_metadata(). Defaults to
            an empty mapping, wrapped in MappingProxyType.
    """

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = DECISION_RECORD_METADATA_VERSION
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    owner: Optional[str] = None
    tags: Sequence[str] = field(default_factory=tuple)
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "tags", tuple(self.tags))
        object.__setattr__(self, "extra", MappingProxyType(dict(self.extra)))
