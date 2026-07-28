"""
Interfaces for the Argus Sales OS Campaigns package.

Purpose:
    Define ICampaignBuilder, the contract for a mutable, fluent
    Campaign builder. Mirrors ICompanyBuilder/IContactBuilder: no new
    Core service is introduced, so ICampaignBuilder does not inherit
    IService.

Responsibilities:
    - ICampaignBuilder: the contract implemented by CampaignBuilder.

Non-Responsibilities:
    - This module defines no concrete behavior - see builder.py.

Dependencies:
    argus.modules.sales.campaigns.campaign (Campaign),
    argus.modules.sales.campaigns.status (CampaignStatus).
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from argus.modules.sales.campaigns.campaign import Campaign
from argus.modules.sales.campaigns.status import CampaignStatus


class ICampaignBuilder(ABC):
    """
    Contract for a mutable, fluent Campaign builder.
    """

    @abstractmethod
    def with_name(self, name: str) -> "ICampaignBuilder":
        """Set this builder's name. Raises InvalidCampaignError if
        `name` is not a non-empty string."""

    @abstractmethod
    def with_description(self, description: str) -> "ICampaignBuilder":
        """Set this builder's description. Raises InvalidCampaignError
        if `description` is not a string."""

    @abstractmethod
    def with_status(self, status: CampaignStatus) -> "ICampaignBuilder":
        """Set this builder's status. Raises InvalidCampaignError if
        `status` is not a CampaignStatus instance."""

    @abstractmethod
    def with_territory(self, territory: str) -> "ICampaignBuilder":
        """Set this builder's territory. Raises InvalidCampaignError
        if `territory` is not a string."""

    @abstractmethod
    def with_start_date(self, start_date: Optional[datetime]) -> "ICampaignBuilder":
        """Set this builder's start_date. Raises InvalidCampaignError
        if `start_date` is neither None nor a datetime instance."""

    @abstractmethod
    def with_end_date(self, end_date: Optional[datetime]) -> "ICampaignBuilder":
        """Set this builder's end_date. Raises InvalidCampaignError if
        `end_date` is neither None nor a datetime instance."""

    @abstractmethod
    def with_notes(self, notes: str) -> "ICampaignBuilder":
        """Set this builder's notes. Raises InvalidCampaignError if
        `notes` is not a string."""

    @abstractmethod
    def with_metadata(self, key: str, value: Any) -> "ICampaignBuilder":
        """Set one arbitrary metadata key/value pair on the eventual
        CampaignMetadata.extra mapping. Raises InvalidCampaignError if
        `key` is not a non-empty string."""

    @abstractmethod
    def build(self) -> Campaign:
        """Construct and return a fresh, immutable Campaign snapshot
        from this builder's current accumulated state."""
