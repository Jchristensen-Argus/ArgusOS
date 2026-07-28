"""
The ContactMetadata value object for the Argus Sales OS Contacts
package.

Purpose:
    Hold lightweight, descriptive bookkeeping about a single Contact
    instance. Mirrors CompanyMetadata/LeadMetadata's shape and field
    order exactly - see argus.modules.sales.companies.metadata's own
    module docstring for the full rationale.

Responsibilities:
    - ContactMetadata: hold a Contact's own creation timestamp, schema
      version, correlation identifier, and any caller-supplied extra
      data as an immutable value object.

Non-Responsibilities:
    - ContactMetadata performs no computation and holds no runtime
      state.

Dependencies:
    None.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

CONTACT_METADATA_VERSION = "1.0"


@dataclass(frozen=True)
class ContactMetadata:
    """
    Immutable, lightweight bookkeeping about a single Contact
    instance. See the module docstring for the full field semantics.
    """

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = CONTACT_METADATA_VERSION
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra", MappingProxyType(dict(self.extra)))
