"""
Exceptions for the Argus Sales OS Work Queue package.

Purpose:
    Define the error types argus.modules.sales.work_queue itself can
    raise. Mirrors argus.modules.sales.import_pipeline.exceptions's
    shape: a base error plus one specific, named failure case.

Responsibilities:
    - WorkQueueError: the base exception for this package.
    - WorkItemNotFoundError: raised when a caller references a
      work_item_id the WorkQueue does not hold.

Non-Responsibilities:
    - This module performs no logic beyond defining exception types.

Dependencies:
    None.
"""


class WorkQueueError(Exception):
    """Base exception for the argus.modules.sales.work_queue package."""


class WorkItemNotFoundError(WorkQueueError):
    """Raised when start()/complete()/skip() is called with a
    work_item_id the WorkQueue does not currently hold."""
