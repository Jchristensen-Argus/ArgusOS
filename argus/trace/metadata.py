"""
The TraceMetadata value object for the ArgusOS Execution Trace.

Purpose:
    Hold lightweight, descriptive bookkeeping about a single
    ExecutionTrace instance itself - when it was created, what trace
    schema version produced it, and a correlation identifier for
    tracing it - per factory/packages/028_EXECUTION_TRACE.md. "Mirror
    existing metadata conventions." TraceMetadata is pure data: it
    does not compute anything and knows nothing about the
    ExecutionTrace or TraceStep objects it describes.

Mirrors ContextMetadata/PlanningMetadata's Shape And Field Names
Exactly:
    Unlike argus.response.metadata.ResponseMetadata (Package 027),
    whose own work order explicitly named its timestamp field
    `timestamp`, this package's own work order names the field
    `created_at` - the same name argus.context.metadata.ContextMetadata
    (022) and argus.planning.metadata.PlanningMetadata (023) both use.
    This module therefore reverts to the `created_at` naming rather
    than repeating Package 027's one-field deviation. The work order
    itself lists this field set as "version, correlation_id,
    created_at" (in that order); this module declares them in the
    same relative order Context/PlanningMetadata use instead
    (`created_at`, `version`, `correlation_id`, `extra`), since "mirror
    existing metadata conventions" is the dominant instruction and a
    literal field listing elsewhere in the same work order is not
    itself a required declaration order (all four fields carry
    defaults, so no ordering constraint forces a particular sequence
    either way). The `extra` mapping is not named in this package's
    own explicit field list, exactly as it was not named in Package
    027's; it is included anyway for the same reason: every prior
    sibling metadata class ends with one, and TraceBuilder.with_metadata()
    needs somewhere to accumulate into.

Responsibilities:
    - TraceMetadata: hold an ExecutionTrace's own creation timestamp,
      schema version, correlation identifier, and any caller-supplied
      extra data as an immutable value object.

Non-Responsibilities:
    - TraceMetadata performs no computation and holds no runtime
      state - not a snapshot of any live service, not a cache.
    - This module has no dependency on any other argus.trace module,
      matching the "pure, dependency-free leaf" precedent set by every
      other metadata value object in this codebase.

Dependencies:
    None.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

#: The trace schema version this module produces. Not related to
#: CORE_SERVICES_VERSION (argus/bootstrap.py) - this versions the
#: shape of TraceMetadata/ExecutionTrace itself. Mirrors
#: CONTEXT_METADATA_VERSION / PLANNING_METADATA_VERSION /
#: RESPONSE_METADATA_VERSION's identical role.
TRACE_METADATA_VERSION = "1.0"


@dataclass(frozen=True)
class TraceMetadata:
    """
    Immutable, lightweight bookkeeping about a single ExecutionTrace
    instance. See the module docstring for the full field semantics.

    Fields:
        created_at: The UTC timestamp this TraceMetadata was
            constructed. Defaults to the current time.
        version: The trace schema version that produced this
            metadata. Defaults to TRACE_METADATA_VERSION.
        correlation_id: An identifier for tracing the owning
            ExecutionTrace. Defaults to a fresh uuid4 string.
        extra: Any additional caller-supplied data. Defaults to an
            empty mapping.
    """

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = TRACE_METADATA_VERSION
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra", MappingProxyType(dict(self.extra)))
