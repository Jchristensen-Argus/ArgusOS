"""
The Lead value object for the Argus Sales OS Lead Workspace.

Purpose:
    Represent a single sales lead as an immutable value object, per
    ARGUS_SALES_OS_V1_ARCHITECTURE.md's Sprint 1 scope: "load the Lead
    Workspace spreadsheet, parse every lead into canonical Lead
    objects." Mirrors argus.task.task.Task's own shape: a frozen
    dataclass, every field defaulted so Lead() is always valid, no
    validation of its own beyond typing - see builder.py for where
    malformed input is rejected.

Every Field Defaults - Lead() Is Always Valid:
    Same "value object with a dedicated builder" shape Task (029),
    CognitiveContext (022), PlanningSession (023), and ExecutionTrace
    (028) all use. `lead_id` defaults to a fresh uuid4 string; every
    other identifying field defaults to an empty string; `status`
    defaults to LeadStatus.NEW; `sync_state` defaults to
    LeadSyncState.NOT_SYNCED; `next_touch_date`/`last_touch_date`
    default to None (no touch scheduled/recorded yet); `metadata`
    defaults to a fresh LeadMetadata.

Company and Contact Are Referenced By Id, Not Embedded:
    Per ARGUS_SALES_OS_V1_ARCHITECTURE.md, Company and Contact are
    their own canonical data models (Slice 2), not fields embedded on
    Lead - a Lead references `company_id`/`contact_id`. This avoids
    duplicating a Company's or Contact's own fields onto every Lead
    that references them, the same "one concept, one authoritative
    home" discipline (Cognitive Architecture, CA-12) applied to data
    modeling rather than documentation.

No Validation Here - See builder.py:
    Like every other value object in this codebase, Lead performs no
    validation of its own fields in `__post_init__` beyond the
    standard `metadata` typing. LeadBuilder's own with_*() methods are
    where malformed input is rejected.

Filterable By Design:
    `status`, `next_touch_date`, `campaign_id`, `territory`, and
    `sync_state` are exactly the five fields
    ARGUS_SALES_OS_V1_ARCHITECTURE.md names as the Sprint 1 work
    queue's required filters - "filter by status/next-touch-date/
    campaign/territory/synchronization-state." No filtering logic
    lives here; see the future work-queue module (Slice 4).

Responsibilities:
    - Lead: hold identity (`lead_id`), references to its Company and
      Contact, its Campaign, its own `status`, `territory`, `source`,
      touch-scheduling dates, its Dynamics sync bookkeeping, free-text
      `notes`, and descriptive LeadMetadata, as an immutable value
      object.

Non-Responsibilities:
    - Lead performs no reasoning, scheduling, dispatch, or
      synchronization of any kind.
    - Lead does not construct, obtain, or reference any Company,
      Contact, Campaign, or Dynamics Connector - it holds only their
      ids, matching the "pure, dependency-free leaf" precedent set by
      Task's own relationship to TaskRelationship.

Dependencies:
    argus.modules.sales.leads.status (LeadStatus),
    argus.modules.sales.leads.sync_state (LeadSyncState),
    argus.modules.sales.leads.metadata (LeadMetadata).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from argus.modules.sales.leads.metadata import LeadMetadata
from argus.modules.sales.leads.status import LeadStatus
from argus.modules.sales.leads.sync_state import LeadSyncState


@dataclass(frozen=True)
class Lead:
    """
    An immutable record of one sales lead. See the module docstring
    for the full field semantics.

    Fields:
        lead_id: Unique identifier for this Lead. Defaults to a fresh
            uuid4 string.
        company_id: The id of the Company this Lead belongs to.
            Defaults to an empty string (unassigned).
        contact_id: The id of the Contact this Lead belongs to.
            Defaults to an empty string (unassigned).
        campaign_id: The id of the Campaign this Lead is being worked
            under, if any. Defaults to an empty string (unassigned).
        status: This Lead's current LeadStatus. Defaults to
            LeadStatus.NEW.
        territory: A free-text territory label for filtering/routing.
            Defaults to an empty string.
        source: Where this Lead originated - e.g. "zoominfo",
            "dynamics", "manual". Defaults to an empty string.
        next_touch_date: When this Lead is next due for outreach, if
            scheduled. Defaults to None.
        last_touch_date: When this Lead was last touched, if ever.
            Defaults to None.
        dynamics_record_id: The external Dynamics record id this Lead
            corresponds to, once synced. Defaults to an empty string.
        sync_state: This Lead's current LeadSyncState. Defaults to
            LeadSyncState.NOT_SYNCED.
        notes: Free-text notes. Defaults to an empty string.
        metadata: Descriptive bookkeeping about this Lead. Defaults to
            a fresh LeadMetadata.
    """

    lead_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    contact_id: str = ""
    campaign_id: str = ""
    status: LeadStatus = LeadStatus.NEW
    territory: str = ""
    source: str = ""
    next_touch_date: Optional[datetime] = None
    last_touch_date: Optional[datetime] = None
    dynamics_record_id: str = ""
    sync_state: LeadSyncState = LeadSyncState.NOT_SYNCED
    notes: str = ""
    metadata: LeadMetadata = field(default_factory=LeadMetadata)
