"""
The ContextMetadata value object for the ArgusOS Cognitive Context.

Purpose:
    Hold lightweight, descriptive bookkeeping about a single
    CognitiveContext instance itself - when it was created, what
    context schema version produced it, a correlation identifier for
    tracing it across the cognitive pipeline, and any additional
    caller-supplied metadata - per
    factory/packages/022_COGNITIVE_CONTEXT.md. "Keep it lightweight.
    No runtime state." ContextMetadata is pure data: it does not
    compute, validate its own creation timestamp against a clock at
    read time, or know anything about the CognitiveContext it
    describes.

Two Kinds Of Metadata, Reconciled Into One Field:
    The work order's Responsibilities section lists "arbitrary
    metadata" as one of the things a CognitiveContext shall carry,
    while its own Metadata section separately describes
    ContextMetadata as holding specific, named fields ("creation
    timestamp, version, correlation identifier"). This module
    reconciles both: ContextMetadata holds those three named fields
    directly, plus one additional `extra` mapping for genuinely
    open-ended, caller-supplied key/value data - so
    `CognitiveContext.metadata` (typed as ContextMetadata, not a bare
    dict) satisfies both descriptions with a single field, rather
    than requiring two separate metadata-shaped fields on
    CognitiveContext itself. ContextBuilder.with_metadata() only ever
    populates `extra`; `created_at`, `version`, and `correlation_id`
    are system-assigned at construction time, not caller-settable
    through the builder's fluent interface (see builder.py's own
    docstring).

Responsibilities:
    - ContextMetadata: hold a CognitiveContext's own creation
      timestamp, schema version, correlation identifier, and
      arbitrary extra metadata as an immutable value object.

Non-Responsibilities:
    - ContextMetadata performs no computation and holds no runtime
      state - not a snapshot of any live service, not a cache, and
      not a reference back to the CognitiveContext it describes.
    - This module has no dependency on any other argus.context
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

#: The Cognitive Context schema version this module produces. Not
#: related to CORE_SERVICES_VERSION (argus/bootstrap.py) - this
#: versions the shape of ContextMetadata/CognitiveContext itself, in
#: case a future package needs to distinguish contexts produced by
#: different schema revisions.
CONTEXT_METADATA_VERSION = "1.0"


@dataclass(frozen=True)
class ContextMetadata:
    """
    Immutable, lightweight bookkeeping about a single CognitiveContext
    instance. See the module docstring for the full field semantics.

    Fields:
        created_at: The UTC timestamp this ContextMetadata was
            constructed. Defaults to the current time.
        version: The Cognitive Context schema version that produced
            this metadata. Defaults to CONTEXT_METADATA_VERSION.
        correlation_id: An identifier for tracing the owning
            CognitiveContext across the cognitive pipeline. Defaults
            to a fresh uuid4 string.
        extra: Additional, arbitrary caller-supplied metadata.
            Defaults to an empty mapping.
    """

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = CONTEXT_METADATA_VERSION
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra", MappingProxyType(dict(self.extra)))
