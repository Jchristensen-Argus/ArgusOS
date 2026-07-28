"""
argus.modules.sales.work_queue - The Lead Workspace work queue
(Sprint 1, Slice 4).

Re-exports the public surface: WorkQueue, order_work_items, and this
package's own exceptions. See ARGUS_SALES_OS_V1_ARCHITECTURE.md for the
full architectural rationale, and work_queue.py's own In-Memory Only
note before treating a WorkQueue instance as durable.
"""

from argus.modules.sales.work_queue.exceptions import (
    WorkItemNotFoundError,
    WorkQueueError,
)
from argus.modules.sales.work_queue.ordering import order_work_items
from argus.modules.sales.work_queue.work_queue import WorkQueue

__all__ = [
    "WorkQueue",
    "order_work_items",
    "WorkQueueError",
    "WorkItemNotFoundError",
]
