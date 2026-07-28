"""
The WorkItemMetadata value object for the Argus Sales OS Work Items
package.

Purpose:
    Hold lightweight, descriptive bookkeeping about a single WorkItem
    instance. Mirrors CampaignMetadata/CompanyMetadata/ContactMetadata/
    LeadMetadata's shape and field order exactly.

Responsibilities:
    - WorkItemMetadata: hold a WorkItem's own creation timestamp,
      schema version, correlation identifier, and any caller-supplied
      extra data as an immutable value object.

Non-Responsibilities:
    - WorkItemMetadata performs no computation and holds no runtime
      state.

Dependencies:
    None.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

WORK_ITEM_METADATA_VERSION = "1.0"


@dataclass(frozen=True)
class WorkItemMetadata:
    """
    Immutable, lightweight bookkeeping about a single WorkItem
    instance. See the module docstring for the full field semantics.
    """

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = WORK_ITEM_METADATA_VERSION
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra", MappingProxyType(dict(self.extra)))
