"""
The WorkItemBuilder for the Argus Sales OS Work Items package.

Purpose:
    Provide a mutable, fluent way to assemble a WorkItem's fields one
    at a time before producing a single immutable WorkItem snapshot.
    Directly mirrors argus.modules.sales.campaigns.builder.CampaignBuilder,
    except no field here is required non-empty - unlike a Campaign or
    Company, a WorkItem with every field defaulted (type OTHER,
    unassigned lead_id) is still a legitimate placeholder, matching
    Lead's and Contact's own "every field may default" posture.

Responsibilities:
    - WorkItemBuilder: assign a WorkItem's fields one at a time, with
      per-field validation, and produce an immutable WorkItem snapshot
      on build().

Non-Responsibilities:
    - WorkItemBuilder performs no reasoning, scheduling, or execution
      of any kind - it only validates and assigns plain data.
    - WorkItemBuilder is not a service.

Dependencies:
    argus.modules.sales.work_items.work_item (WorkItem),
    argus.modules.sales.work_items.work_type (WorkItemType),
    argus.modules.sales.work_items.status (WorkItemStatus),
    argus.modules.sales.work_items.metadata (WorkItemMetadata),
    argus.modules.sales.work_items.exceptions (InvalidWorkItemError),
    argus.modules.sales.work_items.interfaces (IWorkItemBuilder).
"""

from datetime import datetime
from typing import Any, Dict, Optional

from argus.modules.sales.work_items.exceptions import InvalidWorkItemError
from argus.modules.sales.work_items.interfaces import IWorkItemBuilder
from argus.modules.sales.work_items.metadata import WorkItemMetadata
from argus.modules.sales.work_items.status import WorkItemStatus
from argus.modules.sales.work_items.work_item import WorkItem
from argus.modules.sales.work_items.work_type import WorkItemType


def _require_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str):
        raise InvalidWorkItemError(f"{label} must be a string, got {value!r}.")
    return value


def _require_optional_datetime(value: Any, *, label: str) -> Optional[datetime]:
    if value is not None and not isinstance(value, datetime):
        raise InvalidWorkItemError(
            f"{label} must be None or a datetime instance, got {value!r}."
        )
    return value


class WorkItemBuilder(IWorkItemBuilder):
    """
    A mutable, fluent builder for WorkItem. See the module docstring
    for the full assignment and validation semantics.
    """

    def __init__(self) -> None:
        self._lead_id: str = ""
        self._work_type: WorkItemType = WorkItemType.OTHER
        self._status: WorkItemStatus = WorkItemStatus.PENDING
        self._due_date: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None
        self._notes: str = ""
        self._metadata_extra: Dict[str, Any] = {}

    def with_lead_id(self, lead_id: str) -> "WorkItemBuilder":
        self._lead_id = _require_string(lead_id, label="lead_id")
        return self

    def with_work_type(self, work_type: WorkItemType) -> "WorkItemBuilder":
        if not isinstance(work_type, WorkItemType):
            raise InvalidWorkItemError(
                f"work_type must be a WorkItemType instance, got {work_type!r}."
            )
        self._work_type = work_type
        return self

    def with_status(self, status: WorkItemStatus) -> "WorkItemBuilder":
        if not isinstance(status, WorkItemStatus):
            raise InvalidWorkItemError(
                f"status must be a WorkItemStatus instance, got {status!r}."
            )
        self._status = status
        return self

    def with_due_date(self, due_date: Optional[datetime]) -> "WorkItemBuilder":
        self._due_date = _require_optional_datetime(due_date, label="due_date")
        return self

    def with_completed_at(
        self, completed_at: Optional[datetime]
    ) -> "WorkItemBuilder":
        self._completed_at = _require_optional_datetime(
            completed_at, label="completed_at"
        )
        return self

    def with_notes(self, notes: str) -> "WorkItemBuilder":
        self._notes = _require_string(notes, label="notes")
        return self

    def with_metadata(self, key: str, value: Any) -> "WorkItemBuilder":
        if not isinstance(key, str) or not key:
            raise InvalidWorkItemError(
                f"metadata key must be a non-empty string, got {key!r}."
            )
        self._metadata_extra[key] = value
        return self

    def build(self) -> WorkItem:
        return WorkItem(
            lead_id=self._lead_id,
            work_type=self._work_type,
            status=self._status,
            due_date=self._due_date,
            completed_at=self._completed_at,
            notes=self._notes,
            metadata=WorkItemMetadata(extra=dict(self._metadata_extra)),
        )
