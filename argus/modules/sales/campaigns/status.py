"""
The CampaignStatus enumeration for the Argus Sales OS Campaigns
package.

Purpose:
    Represent the closed set of states a Campaign may carry, per
    ARGUS_SALES_OS_V1_ARCHITECTURE.md. Mirrors LeadStatus's own shape:
    a plain `Enum`, lowercase string values, no automatic transitions
    - a caller sets status explicitly via CampaignBuilder.with_status().

Responsibilities:
    - CampaignStatus: enumerate the states a Campaign's own `status`
      field may hold.

Non-Responsibilities:
    - This module implements no transition logic.

Dependencies:
    None.
"""

from enum import Enum


class CampaignStatus(Enum):
    """
    The closed set of states a Campaign may be in.

    DRAFT: being planned, not yet active - the default.
    ACTIVE: currently being worked.
    PAUSED: temporarily suspended, expected to resume.
    COMPLETED: finished, no longer being worked.
    """

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
