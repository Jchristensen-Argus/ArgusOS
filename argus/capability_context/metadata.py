"""
The CapabilityContextMetadata value object for the ArgusOS Capability
Context.

Purpose:
    Hold lightweight, descriptive bookkeeping about a single
    CapabilityContext instance itself - when it was created, what
    schema version produced it, and a correlation identifier for
    tracing it - per factory/packages/035_CAPABILITY_CONTEXT.md.
    "Follow existing metadata conventions." CapabilityContextMetadata
    is pure data: it does not compute anything and knows nothing about
    the Task, Plan, or ExecutionTrace the CapabilityContext it
    describes actually references.

Mirrors Every Sibling Metadata Module's Shape And Field Names Exactly:
    This package's own explicit field list is "created_at,
    correlation_id, version, extra" - the same relative order named
    (and then normalized away from) by Packages 028, 029, 031, 032,
    033, and 034's own equivalent metadata modules. This package's own
    work order explicitly instructs "Follow existing metadata
    conventions" - the same explicit instruction Package 034's own
    CapabilityExecutionMetadata already received, settling directly,
    without any interpretive judgment call, the same field-order
    tension every metadata-bearing package since 028 has had to reason
    its own way through. This module declares fields in the same
    relative order every sibling metadata module uses (`created_at`,
    `version`, `correlation_id`, `extra`), not the order listed above.

Responsibilities:
    - CapabilityContextMetadata: hold a CapabilityContext's own
      creation timestamp, schema version, correlation identifier, and
      any caller-supplied extra data as an immutable value object.

Non-Responsibilities:
    - CapabilityContextMetadata performs no computation and holds no
      runtime state - not a snapshot of any live service, not a
      cache.
    - This module has no dependency on any other
      argus.capability_context module, matching the "pure,
      dependency-free leaf" precedent set by every other metadata
      value object in this codebase.

Dependencies:
    None.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

#: The CapabilityContext schema version this module produces. Not
#: related to CORE_SERVICES_VERSION (argus/bootstrap.py) - this
#: versions the shape of CapabilityContextMetadata/CapabilityContext
#: itself. Mirrors every sibling *_METADATA_VERSION constant's
#: identical role.
CAPABILITY_CONTEXT_METADATA_VERSION = "1.0"


@dataclass(frozen=True)
class CapabilityContextMetadata:
    """
    Immutable, lightweight bookkeeping about a single CapabilityContext
    instance. See the module docstring for the full field semantics.

    Fields:
        created_at: The UTC timestamp this CapabilityContextMetadata
            was constructed. Defaults to the current time.
        version: The CapabilityContext schema version that produced
            this metadata. Defaults to
            CAPABILITY_CONTEXT_METADATA_VERSION.
        correlation_id: An identifier for tracing the owning
            CapabilityContext. Defaults to a fresh uuid4 string.
        extra: Any additional caller-supplied data. Defaults to an
            empty mapping.
    """

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = CAPABILITY_CONTEXT_METADATA_VERSION
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra", MappingProxyType(dict(self.extra)))
