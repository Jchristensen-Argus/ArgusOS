"""
The TaskMetadata value object for the ArgusOS Task Model.

Purpose:
    Hold lightweight, descriptive bookkeeping about a single Task
    instance itself - when it was created, what schema version
    produced it, and a correlation identifier for tracing it - per
    factory/packages/029_TASK_MODEL.md. "Mirror existing metadata
    conventions." TaskMetadata is pure data: it does not compute
    anything and knows nothing about the Task it describes.

Mirrors ContextMetadata/PlanningMetadata/TraceMetadata's Shape And
Field Names Exactly:
    This package's own explicit field list is "created_at,
    correlation_id, version, extra" - a different relative order than
    argus.context.metadata.ContextMetadata (022),
    argus.planning.metadata.PlanningMetadata (023), and
    argus.trace.metadata.TraceMetadata (028) all use
    (`created_at`, `version`, `correlation_id`, `extra`). Continuing
    the exact reasoning Package 028 already applied to this same
    tension: "mirror existing metadata conventions" is the dominant
    instruction, and a field listed in a different order elsewhere in
    the same work order is not itself a required declaration order
    (every field carries a default, so no ordering constraint forces
    a particular sequence either way) - this module declares fields in
    the same relative order its three siblings use, rather than the
    order listed here.

Responsibilities:
    - TaskMetadata: hold a Task's own creation timestamp, schema
      version, correlation identifier, and any caller-supplied extra
      data as an immutable value object.

Non-Responsibilities:
    - TaskMetadata performs no computation and holds no runtime
      state - not a snapshot of any live service, not a cache.
    - This module has no dependency on any other argus.task module,
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

#: The Task schema version this module produces. Not related to
#: CORE_SERVICES_VERSION (argus/bootstrap.py) - this versions the
#: shape of TaskMetadata/Task itself. Mirrors CONTEXT_METADATA_VERSION
#: / PLANNING_METADATA_VERSION / TRACE_METADATA_VERSION's identical
#: role.
TASK_METADATA_VERSION = "1.0"


@dataclass(frozen=True)
class TaskMetadata:
    """
    Immutable, lightweight bookkeeping about a single Task instance.
    See the module docstring for the full field semantics.

    Fields:
        created_at: The UTC timestamp this TaskMetadata was
            constructed. Defaults to the current time.
        version: The Task schema version that produced this metadata.
            Defaults to TASK_METADATA_VERSION.
        correlation_id: An identifier for tracing the owning Task.
            Defaults to a fresh uuid4 string.
        extra: Any additional caller-supplied data. Defaults to an
            empty mapping.
    """

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = TASK_METADATA_VERSION
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra", MappingProxyType(dict(self.extra)))
