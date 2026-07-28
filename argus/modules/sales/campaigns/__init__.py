"""
argus.modules.sales.campaigns - The Campaigns domain model (Sprint 1,
Slice 2).

Re-exports the public surface: Campaign, CampaignStatus,
CampaignMetadata, the mutable builder (CampaignBuilder) and its
interface (ICampaignBuilder), and this package's own exceptions. See
ARGUS_SALES_OS_V1_ARCHITECTURE.md for the full architectural
rationale.
"""

from argus.modules.sales.campaigns.builder import CampaignBuilder
from argus.modules.sales.campaigns.campaign import Campaign
from argus.modules.sales.campaigns.exceptions import (
    CampaignError,
    InvalidCampaignError,
)
from argus.modules.sales.campaigns.interfaces import ICampaignBuilder
from argus.modules.sales.campaigns.metadata import (
    CAMPAIGN_METADATA_VERSION,
    CampaignMetadata,
)
from argus.modules.sales.campaigns.status import CampaignStatus

__all__ = [
    "Campaign",
    "CampaignStatus",
    "CampaignMetadata",
    "CAMPAIGN_METADATA_VERSION",
    "CampaignBuilder",
    "ICampaignBuilder",
    "CampaignError",
    "InvalidCampaignError",
]
