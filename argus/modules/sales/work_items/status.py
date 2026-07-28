"""
The WorkItemStatus enumeration for the Argus Sales OS Work Items
package.

Purpose:
    Represent the closed set of states a WorkItem may carry, per
    ARGUS_SALES_OS_V1_ARCHITECTURE.md's work-queue scope. Mirrors
    LeadStatus/CampaignStatus's own shape: a plain `Enum`, lowercase
    string values, no automatic transitions.

Responsibilities:
    - WorkItemStatus: enumerate the states a WorkItem's own `status`
      field may hold.

Non-Responsibilities:
    - This module implements no transition logic and no scheduling of
      any kind - see the future work-queue module (Slice 4) for where
      WorkItems are actually surfaced and ordered.

Dependencies:
    None.
"""

from enum import Enum


class WorkItemStatus(Enum):
    """
    The closed set of states a WorkItem may be in.

    PENDING: not yet started - the default.
    IN_PROGRESS: currently being worked.
    COMPLETED: finished.
    SKIPPED: deliberately passed over without completion.
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
