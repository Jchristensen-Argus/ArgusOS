"""
argus.modules.sales.work_items - The Work Items domain model (Sprint
1, Slice 2).

Re-exports the public surface: WorkItem, WorkItemType, WorkItemStatus,
WorkItemMetadata, the mutable builder (WorkItemBuilder) and its
interface (IWorkItemBuilder), and this package's own exceptions. See
ARGUS_SALES_OS_V1_ARCHITECTURE.md for the full architectural
rationale.
"""

from argus.modules.sales.work_items.builder import WorkItemBuilder
from argus.modules.sales.work_items.exceptions import (
    InvalidWorkItemError,
    WorkItemError,
)
from argus.modules.sales.work_items.interfaces import IWorkItemBuilder
from argus.modules.sales.work_items.metadata import (
    WORK_ITEM_METADATA_VERSION,
    WorkItemMetadata,
)
from argus.modules.sales.work_items.status import WorkItemStatus
from argus.modules.sales.work_items.work_item import WorkItem
from argus.modules.sales.work_items.work_type import WorkItemType

__all__ = [
    "WorkItem",
    "WorkItemType",
    "WorkItemStatus",
    "WorkItemMetadata",
    "WORK_ITEM_METADATA_VERSION",
    "WorkItemBuilder",
    "IWorkItemBuilder",
    "WorkItemError",
    "InvalidWorkItemError",
]
