"""
The CapabilityMetadata value object for the ArgusOS Capability
Framework.

Purpose:
    Hold lightweight, descriptive bookkeeping about a single
    Capability instance itself - when it was created, what schema
    version produced it, and a correlation identifier for tracing it
    - per factory/packages/033_CAPABILITY_FRAMEWORK.md. "Follow
    existing metadata conventions." CapabilityMetadata is pure data:
    it does not compute anything and knows nothing about what a
    Capability actually does.

Mirrors ContextMetadata/PlanningMetadata/TraceMetadata/TaskMetadata/
RelationshipMetadata/ExecutionMetadata's Shape And Field Names
Exactly:
    This package's own explicit field list is "created_at,
    correlation_id, version, extra" - the same relative order named
    (and then normalized away from) by every metadata module since
    Package 028. Continuing that same reasoning a fifth time: "follow
    existing metadata conventions" is the dominant instruction, and
    since every field defaults, no ordering constraint forces one
    sequence over the other - this module declares fields in the same
    relative order ContextMetadata/PlanningMetadata/TraceMetadata/
    TaskMetadata/RelationshipMetadata/ExecutionMetadata all use
    (`created_at`, `version`, `correlation_id`, `extra`), not the
    order listed here.

Why This Is A New Field On Capability, Not A Retyping Of The
Pre-Existing `metadata` Field:
    Capability (Package 013) already has a field named `metadata:
    Mapping[str, Any]` - arbitrary, free-form caller-supplied data,
    with no dedicated value-object type, predating the "dedicated
    *Metadata sibling" convention this codebase established starting
    with Package 022. Per the Founder's explicit instruction to
    "extend the existing package... preserving backward compatibility
    wherever practical," retyping that pre-existing field to
    CapabilityMetadata would break every existing caller and test
    that constructs `Capability(metadata={...})` expecting a plain
    mapping back (see tests/test_capability.py's own
    `MappingProxyType`/subscript assertions, unmodified by this
    package). Instead, `Capability` gains a second, new field,
    `capability_metadata: CapabilityMetadata`, declared after the
    pre-existing `metadata` field - satisfying this package's own
    "metadata last" requirement from the perspective of the
    dedicated-metadata-object family this module belongs to, while
    leaving the pre-existing `metadata` field's own type, position,
    and behavior completely untouched. See capability.py's own module
    docstring for the full reconciliation, and
    factory/packages/033_CAPABILITY_FRAMEWORK.md's own Engineering
    Decision section for the complete reasoning.

Responsibilities:
    - CapabilityMetadata: hold a Capability's own creation timestamp,
      schema version, correlation identifier, and any caller-supplied
      extra data as an immutable value object.

Non-Responsibilities:
    - CapabilityMetadata performs no computation and holds no runtime
      state - not a snapshot of any live service, not a cache.
    - This module has no dependency on any other argus.capability
      module, matching the "pure, dependency-free leaf" precedent set
      by every other metadata value object in this codebase.

Dependencies:
    None.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

#: The Capability schema version this module produces. Not related to
#: CORE_SERVICES_VERSION (argus/bootstrap.py) - this versions the
#: shape of CapabilityMetadata/Capability itself. Mirrors
#: CONTEXT_METADATA_VERSION / PLANNING_METADATA_VERSION /
#: TRACE_METADATA_VERSION / TASK_METADATA_VERSION /
#: RELATIONSHIP_METADATA_VERSION / EXECUTION_METADATA_VERSION's
#: identical role.
CAPABILITY_METADATA_VERSION = "1.0"


@dataclass(frozen=True)
class CapabilityMetadata:
    """
    Immutable, lightweight bookkeeping about a single Capability
    instance. See the module docstring for the full field semantics.

    Fields:
        created_at: The UTC timestamp this CapabilityMetadata was
            constructed. Defaults to the current time.
        version: The Capability schema version that produced this
            metadata. Defaults to CAPABILITY_METADATA_VERSION.
        correlation_id: An identifier for tracing the owning
            Capability. Defaults to a fresh uuid4 string.
        extra: Any additional caller-supplied data. Defaults to an
            empty mapping.
    """

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = CAPABILITY_METADATA_VERSION
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra", MappingProxyType(dict(self.extra)))
