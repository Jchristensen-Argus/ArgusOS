"""
The WorkItem value object for the Argus Sales OS Work Items package.

Purpose:
    Represent a single concrete unit of outreach work against a Lead,
    as an immutable value object, per
    ARGUS_SALES_OS_V1_ARCHITECTURE.md's canonical data models. This is
    the entity the future work queue (Slice 4) actually surfaces and
    orders - a Lead describes who; a WorkItem describes what to do
    about them next. Mirrors Campaign's own shape exactly: a frozen
    dataclass, every field defaulted, no validation of its own beyond
    typing - see builder.py.

Referenced By Id, Not Embedded:
    Same discipline as every other Sales entity - WorkItem holds
    `lead_id` as a plain string, never a live Lead instance or an
    import of argus.modules.sales.leads, keeping both packages free of
    a circular dependency.

Responsibilities:
    - WorkItem: hold identity (`work_item_id`), a reference to its
      Lead (`lead_id`), what kind of work it represents
      (`work_type`), its own `status`, scheduling (`due_date`,
      `completed_at`), free-text `notes`, and descriptive
      WorkItemMetadata, as an immutable value object.

Non-Responsibilities:
    - WorkItem performs no reasoning, scheduling, or execution of any
      kind - it does not place a call or send an email. Ordering and
      filtering WorkItems into a daily queue is the future work-queue
      module's responsibility (Slice 4), not this one's.
    - WorkItem does not reference any Company, Contact, or Campaign
      directly - those relationships are reachable via its Lead.

Dependencies:
    argus.modules.sales.work_items.work_type (WorkItemType),
    argus.modules.sales.work_items.status (WorkItemStatus),
    argus.modules.sales.work_items.metadata (WorkItemMetadata).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from argus.modules.sales.work_items.metadata import WorkItemMetadata
from argus.modules.sales.work_items.status import WorkItemStatus
from argus.modules.sales.work_items.work_type import WorkItemType


@dataclass(frozen=True)
class WorkItem:
    """
    An immutable record of one concrete unit of outreach work. See the
    module docstring for the full field semantics.

    Fields:
        work_item_id: Unique identifier for this WorkItem. Defaults to
            a fresh uuid4 string.
        lead_id: The id of the Lead this WorkItem is against. Defaults
            to an empty string (unassigned).
        work_type: What kind of work this WorkItem represents.
            Defaults to WorkItemType.OTHER.
        status: This WorkItem's current WorkItemStatus. Defaults to
            WorkItemStatus.PENDING.
        due_date: When this WorkItem is due, if scheduled. Defaults to
            None.
        completed_at: When this WorkItem was completed, if ever.
            Defaults to None.
        notes: Free-text notes. Defaults to an empty string.
        metadata: Descriptive bookkeeping about this WorkItem.
            Defaults to a fresh WorkItemMetadata.
    """

    work_item_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str = ""
    work_type: WorkItemType = WorkItemType.OTHER
    status: WorkItemStatus = WorkItemStatus.PENDING
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: str = ""
    metadata: WorkItemMetadata = field(default_factory=WorkItemMetadata)
