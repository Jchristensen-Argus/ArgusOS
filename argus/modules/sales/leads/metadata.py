"""
The LeadMetadata value object for the Argus Sales OS Lead Workspace.

Purpose:
    Hold lightweight, descriptive bookkeeping about a single Lead
    instance itself - when it was created, what schema version
    produced it, and a correlation identifier for tracing it. Mirrors
    argus.task.metadata.TaskMetadata's shape and field order exactly
    ("created_at, version, correlation_id, extra"), continuing the
    same "mirror existing metadata conventions" precedent Package 029
    itself followed from Packages 022/023/028. LeadMetadata is pure
    data: it does not compute anything and knows nothing about the
    Lead it describes.

Responsibilities:
    - LeadMetadata: hold a Lead's own creation timestamp, schema
      version, correlation identifier, and any caller-supplied extra
      data as an immutable value object.

Non-Responsibilities:
    - LeadMetadata performs no computation and holds no runtime
      state - not a snapshot of any live service, not a cache.
    - This module has no dependency on any other
      argus.modules.sales.leads module, matching the "pure,
      dependency-free leaf" precedent set by every metadata value
      object in this codebase.

Dependencies:
    None.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

#: The Lead schema version this module produces. Not related to
#: CORE_SERVICES_VERSION (argus/bootstrap.py) - this versions the
#: shape of LeadMetadata/Lead itself, matching
#: TASK_METADATA_VERSION's identical role for argus.task.
LEAD_METADATA_VERSION = "1.0"


@dataclass(frozen=True)
class LeadMetadata:
    """
    Immutable, lightweight bookkeeping about a single Lead instance.
    See the module docstring for the full field semantics.

    Fields:
        created_at: The UTC timestamp this LeadMetadata was
            constructed. Defaults to the current time.
        version: The Lead schema version that produced this metadata.
            Defaults to LEAD_METADATA_VERSION.
        correlation_id: An identifier for tracing the owning Lead.
            Defaults to a fresh uuid4 string.
        extra: Any additional caller-supplied data. Defaults to an
            empty mapping.
    """

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = LEAD_METADATA_VERSION
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra", MappingProxyType(dict(self.extra)))
