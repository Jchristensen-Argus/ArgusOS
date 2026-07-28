"""
The WorkItemType enumeration for the Argus Sales OS Work Items
package.

Purpose:
    Represent the closed set of kinds of work a WorkItem may
    represent, per ARGUS_SALES_OS_V1_ARCHITECTURE.md's Activity
    vocabulary ("drafted an email for this Lead," "called this
    Lead," etc., generalized into a WorkItem's own `work_type`).

Responsibilities:
    - WorkItemType: enumerate the kinds of work a WorkItem's own
      `work_type` field may hold.

Non-Responsibilities:
    - This module implements no execution of any kind - it does not
      place a call, send an email, or perform research. It only
      classifies what a WorkItem represents.

Dependencies:
    None.
"""

from enum import Enum


class WorkItemType(Enum):
    """
    The closed set of kinds of work a WorkItem may represent.

    CALL: an outreach phone call.
    EMAIL: an outreach or follow-up email.
    FOLLOW_UP: a scheduled follow-up touch, method unspecified.
    RESEARCH: prospect intelligence gathering.
    OTHER: anything not covered by the above.
    """

    CALL = "call"
    EMAIL = "email"
    FOLLOW_UP = "follow_up"
    RESEARCH = "research"
    OTHER = "other"
