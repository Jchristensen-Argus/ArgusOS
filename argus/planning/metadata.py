"""
The PlanningMetadata value object for the ArgusOS Planning Session.

Purpose:
    Hold lightweight, descriptive bookkeeping about a single
    PlanningSession instance itself - when it was created, what
    planning schema version produced it, a correlation identifier for
    tracing it across the planning pipeline, and any additional
    caller-supplied metadata - per
    factory/packages/023_PLANNING_SESSION.md. "Remain intentionally
    minimal." PlanningMetadata is pure data: it does not compute,
    validate its own creation timestamp against a clock at read time,
    or know anything about the PlanningSession it describes.

Two Kinds Of Metadata, Reconciled Into One Field:
    Directly reuses the reconciliation `argus.context.metadata.
    ContextMetadata` (Package 022) established for the identical
    tension: this package's own Responsibilities section lists
    "metadata" as one of the things a PlanningSession shall contain,
    while its dedicated Planning Metadata section separately
    describes specific named fields ("creation timestamp, version,
    correlation identifier"). PlanningMetadata holds those three named
    fields directly, plus one additional `extra` mapping for
    genuinely open-ended, caller-supplied key/value data - so
    `PlanningSession.metadata` (typed as PlanningMetadata, not a bare
    dict) satisfies both descriptions with a single field, the same
    resolution `ContextMetadata` already applied. This is the second
    consecutive package to use this exact reconciliation, which is
    worth noting as an emerging convention rather than a coincidence:
    any future package whose work order separately describes
    "arbitrary metadata" and a list of specific named metadata fields
    should very likely reach for the same shape.
    `PlanningSessionBuilder.with_metadata()` only ever populates
    `extra`; `created_at`, `version`, and `correlation_id` are
    system-assigned at construction time, not caller-settable through
    the builder's fluent interface (see builder.py's own docstring).

Responsibilities:
    - PlanningMetadata: hold a PlanningSession's own creation
      timestamp, schema version, correlation identifier, and
      arbitrary extra metadata as an immutable value object.

Non-Responsibilities:
    - PlanningMetadata performs no computation and holds no runtime
      state - not a snapshot of any live service, not a cache, and
      not a reference back to the PlanningSession it describes.
    - This module has no dependency on any other argus.planning
      module, matching the "pure, dependency-free leaf" precedent set
      by every other value object in this codebase.

Dependencies:
    None.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

#: The Planning Session schema version this module produces. Not
#: related to CORE_SERVICES_VERSION (argus/bootstrap.py) - this
#: versions the shape of PlanningMetadata/PlanningSession itself, in
#: case a future package needs to distinguish sessions produced by
#: different schema revisions. Mirrors
#: argus.context.metadata.CONTEXT_METADATA_VERSION's identical role.
PLANNING_METADATA_VERSION = "1.0"


@dataclass(frozen=True)
class PlanningMetadata:
    """
    Immutable, lightweight bookkeeping about a single PlanningSession
    instance. See the module docstring for the full field semantics.

    Fields:
        created_at: The UTC timestamp this PlanningMetadata was
            constructed. Defaults to the current time.
        version: The Planning Session schema version that produced
            this metadata. Defaults to PLANNING_METADATA_VERSION.
        correlation_id: An identifier for tracing the owning
            PlanningSession across the planning pipeline. Defaults to
            a fresh uuid4 string.
        extra: Additional, arbitrary caller-supplied metadata.
            Defaults to an empty mapping.
    """

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = PLANNING_METADATA_VERSION
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra", MappingProxyType(dict(self.extra)))
