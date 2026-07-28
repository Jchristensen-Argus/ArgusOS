"""
argus.modules.sales.leads - The Lead Workspace domain model (Sprint 1,
Slice 1).

Re-exports the public surface: the immutable value objects (Lead,
LeadStatus, LeadSyncState, LeadMetadata), the mutable builder
(LeadBuilder) and its interface (ILeadBuilder), and this package's own
exceptions. See ARGUS_SALES_OS_V1_ARCHITECTURE.md for the full
architectural rationale, and FRAMEWORK_DOCUMENT_LOCATION_CONVENTION.md
(factory/standards/) for why that document is referenced here rather
than duplicated.
"""

from argus.modules.sales.leads.builder import LeadBuilder
from argus.modules.sales.leads.exceptions import InvalidLeadError, LeadError
from argus.modules.sales.leads.interfaces import ILeadBuilder
from argus.modules.sales.leads.lead import Lead
from argus.modules.sales.leads.metadata import LEAD_METADATA_VERSION, LeadMetadata
from argus.modules.sales.leads.status import LeadStatus
from argus.modules.sales.leads.sync_state import LeadSyncState

__all__ = [
    "Lead",
    "LeadStatus",
    "LeadSyncState",
    "LeadMetadata",
    "LEAD_METADATA_VERSION",
    "LeadBuilder",
    "ILeadBuilder",
    "LeadError",
    "InvalidLeadError",
]
