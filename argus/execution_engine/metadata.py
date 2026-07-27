"""
The ExecutionMetadata value object for the ArgusOS Execution Engine.

Purpose:
    Hold lightweight, descriptive bookkeeping about a single
    ExecutionResult instance itself - when it was created, what
    schema version produced it, and a correlation identifier for
    tracing it - per factory/packages/032_EXECUTION_ENGINE.md.
    "Follow existing metadata conventions." ExecutionMetadata is pure
    data: it does not compute anything and knows nothing about the
    Plan or Tasks the ExecutionResult it describes actually covers.

Mirrors ContextMetadata/PlanningMetadata/TraceMetadata/TaskMetadata/
RelationshipMetadata's Shape And Field Names Exactly:
    This package's own explicit field list is "created_at,
    correlation_id, version, extra" - the same relative order named
    (and then normalized away from) by Packages 028, 029, and 031's
    own equivalent metadata modules. Continuing that same reasoning a
    fourth time: "follow existing metadata conventions" is the
    dominant instruction, and since every field defaults, no ordering
    constraint forces one sequence over the other - this module
    declares fields in the same relative order
    ContextMetadata/PlanningMetadata/TraceMetadata/TaskMetadata/
    RelationshipMetadata all use (`created_at`, `version`,
    `correlation_id`, `extra`), not the order listed here.

Responsibilities:
    - ExecutionMetadata: hold an ExecutionResult's own creation
      timestamp, schema version, correlation identifier, and any
      caller-supplied extra data as an immutable value object.

Non-Responsibilities:
    - ExecutionMetadata performs no computation and holds no runtime
      state - not a snapshot of any live service, not a cache.
    - This module has no dependency on any other
      argus.execution_engine module, matching the "pure,
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

#: The ExecutionResult schema version this module produces. Not
#: related to CORE_SERVICES_VERSION (argus/bootstrap.py) - this
#: versions the shape of ExecutionMetadata/ExecutionResult itself.
#: Mirrors CONTEXT_METADATA_VERSION / PLANNING_METADATA_VERSION /
#: TRACE_METADATA_VERSION / TASK_METADATA_VERSION /
#: RELATIONSHIP_METADATA_VERSION's identical role.
EXECUTION_METADATA_VERSION = "1.0"


@dataclass(frozen=True)
class ExecutionMetadata:
    """
    Immutable, lightweight bookkeeping about a single ExecutionResult
    instance. See the module docstring for the full field semantics.

    Fields:
        created_at: The UTC timestamp this ExecutionMetadata was
            constructed. Defaults to the current time.
        version: The ExecutionResult schema version that produced
            this metadata. Defaults to EXECUTION_METADATA_VERSION.
        correlation_id: An identifier for tracing the owning
            ExecutionResult. Defaults to a fresh uuid4 string.
        extra: Any additional caller-supplied data. Defaults to an
            empty mapping.
    """

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = EXECUTION_METADATA_VERSION
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra", MappingProxyType(dict(self.extra)))
