"""
The LeadBuilder for the Argus Sales OS Lead Workspace.

Purpose:
    Provide a mutable, fluent way to assemble a Lead's fields one at a
    time before producing a single immutable Lead snapshot. Directly
    mirrors argus.task.builder.TaskBuilder - the same fluent-builder
    pattern applied to the Lead Workspace.

Every with_*() Method Is A Singular Field, Overwritten, Not
Accumulated:
    Every Lead field this builder sets is a scalar, not a collection -
    calling any with_*() method more than once simply overwrites the
    previous value, the last call before build() wins. Mirrors
    TaskBuilder.with_name()/with_description()/with_status()'s own
    identical rule.

with_metadata() Only Ever Populates `extra`:
    LeadMetadata's `created_at`, `version`, and `correlation_id`
    fields are system-assigned at Lead construction time (see
    metadata.py's own module docstring) - LeadBuilder exposes no way
    to override them. with_metadata(key, value) adds one key/value
    pair to the eventual LeadMetadata.extra mapping; calling it
    multiple times with different keys accumulates, and calling it
    twice with the same key overwrites that key's value.

Validation Lives Here, Not On Lead:
    See lead.py's own module docstring - Lead performs no validation
    of its own; every with_*() method below validates its argument
    before assigning it, raising InvalidLeadError for malformed input.
    build() itself performs no additional validation.

Independent Snapshots:
    build() constructs a fresh Lead (and a fresh LeadMetadata) from
    this builder's current accumulated state every time it is called.
    Continuing to call with_*() methods on the same builder after
    calling build() - or calling build() more than once - never
    mutates a Lead already returned by an earlier build() call, since
    Lead itself is immutable and each build() call constructs a fresh
    instance.

Responsibilities:
    - LeadBuilder: assign a Lead's fields one at a time, with
      per-field validation, and produce an immutable Lead snapshot on
      build().

Non-Responsibilities:
    - LeadBuilder performs no reasoning, scheduling, dispatch, or
      synchronization of any kind - it only validates and assigns
      plain data.
    - LeadBuilder is not a service - see interfaces.py's own module
      docstring.

Dependencies:
    argus.modules.sales.leads.lead (Lead),
    argus.modules.sales.leads.status (LeadStatus),
    argus.modules.sales.leads.sync_state (LeadSyncState),
    argus.modules.sales.leads.metadata (LeadMetadata),
    argus.modules.sales.leads.exceptions (InvalidLeadError),
    argus.modules.sales.leads.interfaces (ILeadBuilder).
"""

from datetime import datetime
from typing import Any, Dict, Optional

from argus.modules.sales.leads.exceptions import InvalidLeadError
from argus.modules.sales.leads.interfaces import ILeadBuilder
from argus.modules.sales.leads.lead import Lead
from argus.modules.sales.leads.metadata import LeadMetadata
from argus.modules.sales.leads.status import LeadStatus
from argus.modules.sales.leads.sync_state import LeadSyncState


def _require_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str):
        raise InvalidLeadError(f"{label} must be a string, got {value!r}.")
    return value


def _require_optional_datetime(value: Any, *, label: str) -> Optional[datetime]:
    if value is not None and not isinstance(value, datetime):
        raise InvalidLeadError(
            f"{label} must be None or a datetime instance, got {value!r}."
        )
    return value


class LeadBuilder(ILeadBuilder):
    """
    A mutable, fluent builder for Lead. See the module docstring for
    the full assignment and validation semantics.
    """

    def __init__(self) -> None:
        self._company_id: str = ""
        self._contact_id: str = ""
        self._campaign_id: str = ""
        self._status: LeadStatus = LeadStatus.NEW
        self._territory: str = ""
        self._source: str = ""
        self._next_touch_date: Optional[datetime] = None
        self._last_touch_date: Optional[datetime] = None
        self._dynamics_record_id: str = ""
        self._sync_state: LeadSyncState = LeadSyncState.NOT_SYNCED
        self._notes: str = ""
        self._metadata_extra: Dict[str, Any] = {}

    def with_company_id(self, company_id: str) -> "LeadBuilder":
        self._company_id = _require_string(company_id, label="company_id")
        return self

    def with_contact_id(self, contact_id: str) -> "LeadBuilder":
        self._contact_id = _require_string(contact_id, label="contact_id")
        return self

    def with_campaign_id(self, campaign_id: str) -> "LeadBuilder":
        self._campaign_id = _require_string(campaign_id, label="campaign_id")
        return self

    def with_status(self, status: LeadStatus) -> "LeadBuilder":
        if not isinstance(status, LeadStatus):
            raise InvalidLeadError(
                f"status must be a LeadStatus instance, got {status!r}."
            )
        self._status = status
        return self

    def with_territory(self, territory: str) -> "LeadBuilder":
        self._territory = _require_string(territory, label="territory")
        return self

    def with_source(self, source: str) -> "LeadBuilder":
        self._source = _require_string(source, label="source")
        return self

    def with_next_touch_date(
        self, next_touch_date: Optional[datetime]
    ) -> "LeadBuilder":
        self._next_touch_date = _require_optional_datetime(
            next_touch_date, label="next_touch_date"
        )
        return self

    def with_last_touch_date(
        self, last_touch_date: Optional[datetime]
    ) -> "LeadBuilder":
        self._last_touch_date = _require_optional_datetime(
            last_touch_date, label="last_touch_date"
        )
        return self

    def with_dynamics_record_id(self, dynamics_record_id: str) -> "LeadBuilder":
        self._dynamics_record_id = _require_string(
            dynamics_record_id, label="dynamics_record_id"
        )
        return self

    def with_sync_state(self, sync_state: LeadSyncState) -> "LeadBuilder":
        if not isinstance(sync_state, LeadSyncState):
            raise InvalidLeadError(
                f"sync_state must be a LeadSyncState instance, got {sync_state!r}."
            )
        self._sync_state = sync_state
        return self

    def with_notes(self, notes: str) -> "LeadBuilder":
        self._notes = _require_string(notes, label="notes")
        return self

    def with_metadata(self, key: str, value: Any) -> "LeadBuilder":
        if not isinstance(key, str) or not key:
            raise InvalidLeadError(
                f"metadata key must be a non-empty string, got {key!r}."
            )
        self._metadata_extra[key] = value
        return self

    def build(self) -> Lead:
        return Lead(
            company_id=self._company_id,
            contact_id=self._contact_id,
            campaign_id=self._campaign_id,
            status=self._status,
            territory=self._territory,
            source=self._source,
            next_touch_date=self._next_touch_date,
            last_touch_date=self._last_touch_date,
            dynamics_record_id=self._dynamics_record_id,
            sync_state=self._sync_state,
            notes=self._notes,
            metadata=LeadMetadata(extra=dict(self._metadata_extra)),
        )
