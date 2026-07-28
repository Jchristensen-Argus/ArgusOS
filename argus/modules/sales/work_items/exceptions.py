"""
Exceptions for the Argus Sales OS Work Items package.

Purpose:
    Define the error types argus.modules.sales.work_items itself can
    raise. Mirrors argus.modules.sales.campaigns.exceptions's shape.

Responsibilities:
    - WorkItemError: the base exception for this package.
    - InvalidWorkItemError: raised by WorkItemBuilder's with_*()
      methods when given a malformed argument.

Non-Responsibilities:
    - This module performs no logic beyond defining exception types.

Dependencies:
    None.
"""


class WorkItemError(Exception):
    """Base exception for the argus.modules.sales.work_items
    package."""


class InvalidWorkItemError(WorkItemError):
    """Raised when WorkItemBuilder's with_*() methods are given a
    malformed argument."""
