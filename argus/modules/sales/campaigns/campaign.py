"""
The Campaign value object for the Argus Sales OS Campaigns package.

Purpose:
    Represent a single outreach campaign a Lead may be worked under,
    as an immutable value object, per
    ARGUS_SALES_OS_V1_ARCHITECTURE.md's canonical data models. Mirrors
    Company/Contact's own shape exactly: a frozen dataclass, every
    field defaulted so Campaign() is always valid, no validation of
    its own beyond typing - see builder.py.

Referenced By Id, Not Embedded:
    Same discipline as every other Sales entity - Lead holds
    `campaign_id` as a plain string; Campaign never references a Lead
    or imports argus.modules.sales.leads, keeping both packages free
    of a circular dependency.

Responsibilities:
    - Campaign: hold identity (`campaign_id`), descriptive fields
      (`name`, `description`, `territory`), its own `status`,
      scheduling dates (`start_date`, `end_date`), free-text `notes`,
      and descriptive CampaignMetadata, as an immutable value object.

Non-Responsibilities:
    - Campaign performs no reasoning, scheduling, or synchronization
      of any kind - it holds only its own descriptive fields.
    - Campaign does not reference any Lead, Contact, or Company.

Dependencies:
    argus.modules.sales.campaigns.status (CampaignStatus),
    argus.modules.sales.campaigns.metadata (CampaignMetadata).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from argus.modules.sales.campaigns.metadata import CampaignMetadata
from argus.modules.sales.campaigns.status import CampaignStatus


@dataclass(frozen=True)
class Campaign:
    """
    An immutable record of one outreach campaign. See the module
    docstring for the full field semantics.

    Fields:
        campaign_id: Unique identifier for this Campaign. Defaults to
            a fresh uuid4 string.
        name: The campaign's name. Defaults to an empty string.
        description: A longer description of this campaign. Defaults
            to an empty string.
        status: This Campaign's current CampaignStatus. Defaults to
            CampaignStatus.DRAFT.
        territory: A free-text territory label, matching Lead's and
            Company's own `territory` field for consistent
            filtering/routing. Defaults to an empty string.
        start_date: When this campaign starts/started, if scheduled.
            Defaults to None.
        end_date: When this campaign ends/ended, if scheduled.
            Defaults to None.
        notes: Free-text notes. Defaults to an empty string.
        metadata: Descriptive bookkeeping about this Campaign.
            Defaults to a fresh CampaignMetadata.
    """

    campaign_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    status: CampaignStatus = CampaignStatus.DRAFT
    territory: str = ""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    notes: str = ""
    metadata: CampaignMetadata = field(default_factory=CampaignMetadata)
