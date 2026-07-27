"""
The CapabilityExecutionMetadata value object for the ArgusOS
Capability Executor.

Purpose:
    Hold lightweight, descriptive bookkeeping about a single
    CapabilityExecutionResult instance itself - when it was created,
    what schema version produced it, and a correlation identifier for
    tracing it - per factory/packages/034_CAPABILITY_EXECUTOR.md.
    "Follow established metadata conventions." CapabilityExecutionMetadata
    is pure data: it does not compute anything and knows nothing about
    the Task or Capability the CapabilityExecutionResult it describes
    actually covers.

Mirrors ContextMetadata/PlanningMetadata/TraceMetadata/TaskMetadata/
RelationshipMetadata/ExecutionMetadata/CapabilityMetadata's Shape And
Field Names Exactly:
    This package's own explicit field list is "created_at,
    correlation_id, version, extra" - the same relative order named
    (and then normalized away from) by Packages 028, 029, 031, 032,
    and 033's own equivalent metadata modules. This package's own
    work order explicitly says "Follow established metadata
    conventions," settling directly what those five prior packages
    each had to reason their own way to: this module declares fields
    in the same relative order every sibling metadata module uses
    (`created_at`, `version`, `correlation_id`, `extra`), not the
    order listed above.

Responsibilities:
    - CapabilityExecutionMetadata: hold a CapabilityExecutionResult's
      own creation timestamp, schema version, correlation identifier,
      and any caller-supplied extra data as an immutable value object.

Non-Responsibilities:
    - CapabilityExecutionMetadata performs no computation and holds no
      runtime state - not a snapshot of any live service, not a
      cache.
    - This module has no dependency on any other
      argus.capability_executor module, matching the "pure,
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

#: The CapabilityExecutionResult schema version this module produces.
#: Not related to CORE_SERVICES_VERSION (argus/bootstrap.py) - this
#: versions the shape of CapabilityExecutionMetadata/
#: CapabilityExecutionResult itself. Mirrors CONTEXT_METADATA_VERSION /
#: PLANNING_METADATA_VERSION / TRACE_METADATA_VERSION /
#: TASK_METADATA_VERSION / RELATIONSHIP_METADATA_VERSION /
#: EXECUTION_METADATA_VERSION / CAPABILITY_METADATA_VERSION's identical
#: role.
CAPABILITY_EXECUTION_METADATA_VERSION = "1.0"


@dataclass(frozen=True)
class CapabilityExecutionMetadata:
    """
    Immutable, lightweight bookkeeping about a single
    CapabilityExecutionResult instance. See the module docstring for
    the full field semantics.

    Fields:
        created_at: The UTC timestamp this CapabilityExecutionMetadata
            was constructed. Defaults to the current time.
        version: The CapabilityExecutionResult schema version that
            produced this metadata. Defaults to
            CAPABILITY_EXECUTION_METADATA_VERSION.
        correlation_id: An identifier for tracing the owning
            CapabilityExecutionResult. Defaults to a fresh uuid4
            string.
        extra: Any additional caller-supplied data. Defaults to an
            empty mapping.
    """

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = CAPABILITY_EXECUTION_METADATA_VERSION
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra", MappingProxyType(dict(self.extra)))
