"""
Interfaces for the Argus Sales OS Work Items package.

Purpose:
    Define IWorkItemBuilder, the contract for a mutable, fluent
    WorkItem builder. Mirrors ICampaignBuilder: no new Core service is
    introduced, so IWorkItemBuilder does not inherit IService.

Responsibilities:
    - IWorkItemBuilder: the contract implemented by WorkItemBuilder.

Non-Responsibilities:
    - This module defines no concrete behavior - see builder.py.

Dependencies:
    argus.modules.sales.work_items.work_item (WorkItem),
    argus.modules.sales.work_items.work_type (WorkItemType),
    argus.modules.sales.work_items.status (WorkItemStatus).
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from argus.modules.sales.work_items.status import WorkItemStatus
from argus.modules.sales.work_items.work_item import WorkItem
from argus.modules.sales.work_items.work_type import WorkItemType


class IWorkItemBuilder(ABC):
    """
    Contract for a mutable, fluent WorkItem builder.
    """

    @abstractmethod
    def with_lead_id(self, lead_id: str) -> "IWorkItemBuilder":
        """Set this builder's lead_id. Raises InvalidWorkItemError if
        `lead_id` is not a string."""

    @abstractmethod
    def with_work_type(self, work_type: WorkItemType) -> "IWorkItemBuilder":
        """Set this builder's work_type. Raises InvalidWorkItemError
        if `work_type` is not a WorkItemType instance."""

    @abstractmethod
    def with_status(self, status: WorkItemStatus) -> "IWorkItemBuilder":
        """Set this builder's status. Raises InvalidWorkItemError if
        `status` is not a WorkItemStatus instance."""

    @abstractmethod
    def with_due_date(self, due_date: Optional[datetime]) -> "IWorkItemBuilder":
        """Set this builder's due_date. Raises InvalidWorkItemError if
        `due_date` is neither None nor a datetime instance."""

    @abstractmethod
    def with_completed_at(
        self, completed_at: Optional[datetime]
    ) -> "IWorkItemBuilder":
        """Set this builder's completed_at. Raises InvalidWorkItemError
        if `completed_at` is neither None nor a datetime instance."""

    @abstractmethod
    def with_notes(self, notes: str) -> "IWorkItemBuilder":
        """Set this builder's notes. Raises InvalidWorkItemError if
        `notes` is not a string."""

    @abstractmethod
    def with_metadata(self, key: str, value: Any) -> "IWorkItemBuilder":
        """Set one arbitrary metadata key/value pair on the eventual
        WorkItemMetadata.extra mapping. Raises InvalidWorkItemError if
        `key` is not a non-empty string."""

    @abstractmethod
    def build(self) -> WorkItem:
        """Construct and return a fresh, immutable WorkItem snapshot
        from this builder's current accumulated state."""
