"""
The CampaignBuilder for the Argus Sales OS Campaigns package.

Purpose:
    Provide a mutable, fluent way to assemble a Campaign's fields one
    at a time before producing a single immutable Campaign snapshot.
    Directly mirrors argus.modules.sales.companies.builder.CompanyBuilder,
    with `name` required non-empty for the same reason ("a Campaign
    with no name is not a usable record on its own").

Responsibilities:
    - CampaignBuilder: assign a Campaign's fields one at a time, with
      per-field validation, and produce an immutable Campaign snapshot
      on build().

Non-Responsibilities:
    - CampaignBuilder performs no reasoning or scheduling logic of its
      own - it only validates and assigns plain data.
    - CampaignBuilder is not a service.

Dependencies:
    argus.modules.sales.campaigns.campaign (Campaign),
    argus.modules.sales.campaigns.status (CampaignStatus),
    argus.modules.sales.campaigns.metadata (CampaignMetadata),
    argus.modules.sales.campaigns.exceptions (InvalidCampaignError),
    argus.modules.sales.campaigns.interfaces (ICampaignBuilder).
"""

from datetime import datetime
from typing import Any, Dict, Optional

from argus.modules.sales.campaigns.campaign import Campaign
from argus.modules.sales.campaigns.exceptions import InvalidCampaignError
from argus.modules.sales.campaigns.interfaces import ICampaignBuilder
from argus.modules.sales.campaigns.metadata import CampaignMetadata
from argus.modules.sales.campaigns.status import CampaignStatus


def _require_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str):
        raise InvalidCampaignError(f"{label} must be a string, got {value!r}.")
    return value


def _require_optional_datetime(value: Any, *, label: str) -> Optional[datetime]:
    if value is not None and not isinstance(value, datetime):
        raise InvalidCampaignError(
            f"{label} must be None or a datetime instance, got {value!r}."
        )
    return value


class CampaignBuilder(ICampaignBuilder):
    """
    A mutable, fluent builder for Campaign. See the module docstring
    for the full assignment and validation semantics.
    """

    def __init__(self) -> None:
        self._name: str = ""
        self._description: str = ""
        self._status: CampaignStatus = CampaignStatus.DRAFT
        self._territory: str = ""
        self._start_date: Optional[datetime] = None
        self._end_date: Optional[datetime] = None
        self._notes: str = ""
        self._metadata_extra: Dict[str, Any] = {}

    def with_name(self, name: str) -> "CampaignBuilder":
        if not isinstance(name, str) or not name:
            raise InvalidCampaignError(
                f"name must be a non-empty string, got {name!r}."
            )
        self._name = name
        return self

    def with_description(self, description: str) -> "CampaignBuilder":
        self._description = _require_string(description, label="description")
        return self

    def with_status(self, status: CampaignStatus) -> "CampaignBuilder":
        if not isinstance(status, CampaignStatus):
            raise InvalidCampaignError(
                f"status must be a CampaignStatus instance, got {status!r}."
            )
        self._status = status
        return self

    def with_territory(self, territory: str) -> "CampaignBuilder":
        self._territory = _require_string(territory, label="territory")
        return self

    def with_start_date(self, start_date: Optional[datetime]) -> "CampaignBuilder":
        self._start_date = _require_optional_datetime(start_date, label="start_date")
        return self

    def with_end_date(self, end_date: Optional[datetime]) -> "CampaignBuilder":
        self._end_date = _require_optional_datetime(end_date, label="end_date")
        return self

    def with_notes(self, notes: str) -> "CampaignBuilder":
        self._notes = _require_string(notes, label="notes")
        return self

    def with_metadata(self, key: str, value: Any) -> "CampaignBuilder":
        if not isinstance(key, str) or not key:
            raise InvalidCampaignError(
                f"metadata key must be a non-empty string, got {key!r}."
            )
        self._metadata_extra[key] = value
        return self

    def build(self) -> Campaign:
        return Campaign(
            name=self._name,
            description=self._description,
            status=self._status,
            territory=self._territory,
            start_date=self._start_date,
            end_date=self._end_date,
            notes=self._notes,
            metadata=CampaignMetadata(extra=dict(self._metadata_extra)),
        )
