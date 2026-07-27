"""
The AutomationMetadata value object for the ArgusOS Automation
Framework.

Purpose:
    Hold lightweight, descriptive bookkeeping about a single
    Automation instance itself - when it was created, what schema
    version produced it, a correlation identifier for tracing it, who
    owns it, and what tags organize it - per
    factory/packages/041_AUTOMATION_FRAMEWORK.md. "Follow the
    established metadata convention." AutomationMetadata is pure
    data: it does not compute anything and knows nothing about what an
    Automation actually does.

Field Order - Following ProjectMetadata/WorkspaceMetadata/GoalMetadata/
DecisionRecordMetadata/PolicyMetadata's Own Precedent, Not This
Package's Own Literal Listed Order:
    This package's own literal field list reads "created_at, owner,
    correlation_id, version, tags, extra" - the identical literal
    order every prior organizational-tier metadata module's own work
    order has used, each resolved in favor of ProjectMetadata's own
    established order instead. This package's own governing
    instruction - "Follow the established metadata convention" - is
    the least specific phrasing yet (037-040 each named specific prior
    packages by name), but by this point in the codebase's own
    history there is only one "established metadata convention" left
    to follow: five consecutive sibling metadata modules
    (ProjectMetadata 036, WorkspaceMetadata 037, GoalMetadata 038,
    DecisionRecordMetadata 039, PolicyMetadata 040) all declare the
    identical six-field order `created_at`, `version`,
    `correlation_id`, `owner`, `tags`, `extra`. AutomationMetadata
    follows that same order a sixth time.

owner/tags Are System-Managed Fields, Not Builder-Overridable - See
builder.py:
    Mirrors every sibling metadata module's own identical precedent:
    AutomationBuilder's own Responsibilities list names exactly
    "assign name, assign description, assign status, assign trigger,
    assign metadata" - one bullet for "assign metadata," not separate
    bullets for "assign owner"/"assign tags."

Responsibilities:
    - AutomationMetadata: hold an Automation's own creation timestamp,
      schema version, correlation identifier, owner, tags, and any
      caller-supplied extra data as an immutable value object.

Non-Responsibilities:
    - AutomationMetadata performs no computation and holds no runtime
      state.
    - AutomationMetadata performs no validation of its own fields
      beyond the standard `extra`/`tags` wrapping in `__post_init__`.

Dependencies:
    None beyond the standard library.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Optional, Sequence

AUTOMATION_METADATA_VERSION = "1.0"


@dataclass(frozen=True)
class AutomationMetadata:
    """
    Immutable, descriptive bookkeeping about a single Automation. See
    the module docstring for the full field semantics and for why
    this module's own declared order follows the established
    six-field convention rather than this package's own literal
    listed order.

    Fields:
        created_at: When this AutomationMetadata (and, in practice,
            the Automation it describes) was created. Defaults to the
            current UTC time.
        version: The schema version of this metadata shape. Defaults
            to AUTOMATION_METADATA_VERSION.
        correlation_id: An opaque identifier for tracing this
            Automation's own metadata across the system. Defaults to a
            fresh uuid4 string.
        owner: A human-readable identifier for who owns this
            Automation. Defaults to None. Not settable via
            AutomationBuilder in Version 1 - see the module docstring.
        tags: Free-form labels organizing this Automation. Defaults to
            an empty tuple. Always stored as a tuple, regardless of
            what sequence type is given. Not settable via
            AutomationBuilder in Version 1 - see the module docstring.
        extra: Caller-supplied key/value data, populated exclusively
            through AutomationBuilder.with_metadata(). Defaults to an
            empty mapping, wrapped in MappingProxyType.
    """

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = AUTOMATION_METADATA_VERSION
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    owner: Optional[str] = None
    tags: Sequence[str] = field(default_factory=tuple)
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "tags", tuple(self.tags))
        object.__setattr__(self, "extra", MappingProxyType(dict(self.extra)))
