"""
Interfaces for the Argus Sales OS Lead Workspace package.

Purpose:
    Define ILeadBuilder, the contract for a mutable, fluent Lead
    builder. Mirrors argus.task.interfaces.ITaskBuilder: this package
    introduces no new Core service, so ILeadBuilder does not inherit
    IService - a builder has no meaningful start/stop lifecycle of its
    own; it is a short-lived, per-use accumulator.

Responsibilities:
    - ILeadBuilder: the contract implemented by LeadBuilder.

Non-Responsibilities:
    - This module defines no concrete behavior - see builder.py.

Dependencies:
    argus.modules.sales.leads.lead (Lead),
    argus.modules.sales.leads.status (LeadStatus),
    argus.modules.sales.leads.sync_state (LeadSyncState).
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from argus.modules.sales.leads.lead import Lead
from argus.modules.sales.leads.status import LeadStatus
from argus.modules.sales.leads.sync_state import LeadSyncState


class ILeadBuilder(ABC):
    """
    Contract for a mutable, fluent Lead builder. See this module's
    docstring for why ILeadBuilder does not inherit IService.
    """

    @abstractmethod
    def with_company_id(self, company_id: str) -> "ILeadBuilder":
        """Set this builder's company_id. A later call overwrites an
        earlier one. Raises InvalidLeadError if `company_id` is not a
        string."""

    @abstractmethod
    def with_contact_id(self, contact_id: str) -> "ILeadBuilder":
        """Set this builder's contact_id. A later call overwrites an
        earlier one. Raises InvalidLeadError if `contact_id` is not a
        string."""

    @abstractmethod
    def with_campaign_id(self, campaign_id: str) -> "ILeadBuilder":
        """Set this builder's campaign_id. A later call overwrites an
        earlier one. Raises InvalidLeadError if `campaign_id` is not a
        string."""

    @abstractmethod
    def with_status(self, status: LeadStatus) -> "ILeadBuilder":
        """Set this builder's status. A later call overwrites an
        earlier one. Raises InvalidLeadError if `status` is not a
        LeadStatus instance."""

    @abstractmethod
    def with_territory(self, territory: str) -> "ILeadBuilder":
        """Set this builder's territory. A later call overwrites an
        earlier one. Raises InvalidLeadError if `territory` is not a
        string."""

    @abstractmethod
    def with_source(self, source: str) -> "ILeadBuilder":
        """Set this builder's source. A later call overwrites an
        earlier one. Raises InvalidLeadError if `source` is not a
        string."""

    @abstractmethod
    def with_next_touch_date(self, next_touch_date: Optional[datetime]) -> "ILeadBuilder":
        """Set this builder's next_touch_date. A later call overwrites
        an earlier one. Raises InvalidLeadError if `next_touch_date`
        is neither None nor a datetime instance."""

    @abstractmethod
    def with_last_touch_date(self, last_touch_date: Optional[datetime]) -> "ILeadBuilder":
        """Set this builder's last_touch_date. A later call overwrites
        an earlier one. Raises InvalidLeadError if `last_touch_date`
        is neither None nor a datetime instance."""

    @abstractmethod
    def with_dynamics_record_id(self, dynamics_record_id: str) -> "ILeadBuilder":
        """Set this builder's dynamics_record_id. A later call
        overwrites an earlier one. Raises InvalidLeadError if
        `dynamics_record_id` is not a string."""

    @abstractmethod
    def with_sync_state(self, sync_state: LeadSyncState) -> "ILeadBuilder":
        """Set this builder's sync_state. A later call overwrites an
        earlier one. Raises InvalidLeadError if `sync_state` is not a
        LeadSyncState instance."""

    @abstractmethod
    def with_notes(self, notes: str) -> "ILeadBuilder":
        """Set this builder's notes. A later call overwrites an
        earlier one. Raises InvalidLeadError if `notes` is not a
        string."""

    @abstractmethod
    def with_metadata(self, key: str, value: Any) -> "ILeadBuilder":
        """Set one arbitrary metadata key/value pair on the eventual
        LeadMetadata.extra mapping. Accumulates across multiple calls;
        the same key overwrites - last call wins. Raises
        InvalidLeadError if `key` is not a non-empty string."""

    @abstractmethod
    def build(self) -> Lead:
        """Construct and return a fresh, immutable Lead snapshot from
        this builder's current accumulated state."""
