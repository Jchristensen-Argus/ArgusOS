"""
The CompanyMetadata value object for the Argus Sales OS Companies
package.

Purpose:
    Hold lightweight, descriptive bookkeeping about a single Company
    instance - when it was created, what schema version produced it,
    and a correlation identifier for tracing it. Mirrors
    argus.modules.sales.leads.metadata.LeadMetadata's shape and field
    order exactly (itself mirroring argus.task.metadata.TaskMetadata),
    continuing this codebase's "dedicated Metadata class per value
    object" convention rather than sharing one across entities, so
    each entity's schema can version independently.

Responsibilities:
    - CompanyMetadata: hold a Company's own creation timestamp, schema
      version, correlation identifier, and any caller-supplied extra
      data as an immutable value object.

Non-Responsibilities:
    - CompanyMetadata performs no computation and holds no runtime
      state.
    - This module has no dependency on any other
      argus.modules.sales.companies module.

Dependencies:
    None.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

#: The Company schema version this module produces.
COMPANY_METADATA_VERSION = "1.0"


@dataclass(frozen=True)
class CompanyMetadata:
    """
    Immutable, lightweight bookkeeping about a single Company
    instance. See the module docstring for the full field semantics.

    Fields:
        created_at: The UTC timestamp this CompanyMetadata was
            constructed. Defaults to the current time.
        version: The Company schema version that produced this
            metadata. Defaults to COMPANY_METADATA_VERSION.
        correlation_id: An identifier for tracing the owning Company.
            Defaults to a fresh uuid4 string.
        extra: Any additional caller-supplied data. Defaults to an
            empty mapping.
    """

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = COMPANY_METADATA_VERSION
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra", MappingProxyType(dict(self.extra)))
