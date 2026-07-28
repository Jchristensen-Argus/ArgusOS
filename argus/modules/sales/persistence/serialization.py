"""
Entity <-> plain-dict serialization for the Argus Sales OS persistence
package.

Purpose:
    Convert each of the five Sales entities (Company, Contact,
    Campaign, Lead, WorkItem) to and from plain, JSON-safe dicts. Pure
    transformation - no file I/O, no Event Bus interaction - mirroring
    the parsing/orchestration split already established twice in this
    module (import_pipeline's row_parser.py vs importer.py; work_queue's
    ordering.py vs work_queue.py): this file is the pure half,
    repository.py is the orchestration half that actually reads/writes
    files.

Why One File For All Five Entities, Not Five Files:
    Unlike row_parser.py or ordering.py (each serving one concern for
    one package), these five (de)serializers are genuinely
    parallel - same shape (id, plain fields, one enum or two, a
    Metadata companion) repeated five times. Splitting them into five
    near-identical one-function files would scatter one concept across
    five places for no navigational benefit; keeping them together
    here is the simpler choice for this specific case.

Responsibilities:
    - company_to_dict / company_from_dict
    - contact_to_dict / contact_from_dict
    - campaign_to_dict / campaign_from_dict
    - lead_to_dict / lead_from_dict
    - work_item_to_dict / work_item_from_dict
    Each *_from_dict raises SalesPersistenceError on a malformed dict.

Non-Responsibilities:
    - This module does not read or write any file - see repository.py.
    - This module does not decide what gets persisted or when - see
      repository.py and persistence/session.py.

Dependencies:
    argus.modules.sales.companies, .contacts, .campaigns, .leads,
    .work_items (the five entity + metadata types),
    argus.modules.sales.persistence.exceptions
    (SalesPersistenceError).
"""

from datetime import datetime
from typing import Any, Dict, Optional, Type, TypeVar

from argus.modules.sales.campaigns.campaign import Campaign
from argus.modules.sales.campaigns.metadata import CampaignMetadata
from argus.modules.sales.campaigns.status import CampaignStatus
from argus.modules.sales.companies.company import Company
from argus.modules.sales.companies.metadata import CompanyMetadata
from argus.modules.sales.contacts.contact import Contact
from argus.modules.sales.contacts.metadata import ContactMetadata
from argus.modules.sales.leads.lead import Lead
from argus.modules.sales.leads.metadata import LeadMetadata
from argus.modules.sales.leads.status import LeadStatus
from argus.modules.sales.leads.sync_state import LeadSyncState
from argus.modules.sales.persistence.exceptions import SalesPersistenceError
from argus.modules.sales.work_items.metadata import WorkItemMetadata
from argus.modules.sales.work_items.status import WorkItemStatus
from argus.modules.sales.work_items.work_item import WorkItem
from argus.modules.sales.work_items.work_type import WorkItemType

_MetadataT = TypeVar("_MetadataT")


def _optional_datetime_to_iso(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value is not None else None


def _optional_iso_to_datetime(value: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(value) if value else None


def _metadata_to_dict(metadata: Any) -> Dict[str, Any]:
    return {
        "created_at": metadata.created_at.isoformat(),
        "version": metadata.version,
        "correlation_id": metadata.correlation_id,
        "extra": dict(metadata.extra),
    }


def _metadata_from_dict(data: Dict[str, Any], metadata_cls: Type[_MetadataT]) -> _MetadataT:
    return metadata_cls(
        created_at=datetime.fromisoformat(data["created_at"]),
        version=data["version"],
        correlation_id=data["correlation_id"],
        extra=data.get("extra", {}),
    )


def _wrap_errors(entity_name: str, data: Dict[str, Any], func):
    try:
        return func()
    except (KeyError, TypeError, ValueError) as error:
        raise SalesPersistenceError(
            f"Malformed {entity_name} record {data!r}: {error}"
        ) from error


# --- Company ---------------------------------------------------------


def company_to_dict(company: Company) -> Dict[str, Any]:
    return {
        "company_id": company.company_id,
        "name": company.name,
        "industry": company.industry,
        "website": company.website,
        "territory": company.territory,
        "notes": company.notes,
        "metadata": _metadata_to_dict(company.metadata),
    }


def company_from_dict(data: Dict[str, Any]) -> Company:
    return _wrap_errors(
        "Company",
        data,
        lambda: Company(
            company_id=data["company_id"],
            name=data["name"],
            industry=data["industry"],
            website=data["website"],
            territory=data["territory"],
            notes=data["notes"],
            metadata=_metadata_from_dict(data["metadata"], CompanyMetadata),
        ),
    )


# --- Contact -----------------------------------------------------------


def contact_to_dict(contact: Contact) -> Dict[str, Any]:
    return {
        "contact_id": contact.contact_id,
        "company_id": contact.company_id,
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "email": contact.email,
        "phone": contact.phone,
        "title": contact.title,
        "notes": contact.notes,
        "metadata": _metadata_to_dict(contact.metadata),
    }


def contact_from_dict(data: Dict[str, Any]) -> Contact:
    return _wrap_errors(
        "Contact",
        data,
        lambda: Contact(
            contact_id=data["contact_id"],
            company_id=data["company_id"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            phone=data["phone"],
            title=data["title"],
            notes=data["notes"],
            metadata=_metadata_from_dict(data["metadata"], ContactMetadata),
        ),
    )


# --- Campaign ------------------------------------------------------------


def campaign_to_dict(campaign: Campaign) -> Dict[str, Any]:
    return {
        "campaign_id": campaign.campaign_id,
        "name": campaign.name,
        "description": campaign.description,
        "status": campaign.status.value,
        "territory": campaign.territory,
        "start_date": _optional_datetime_to_iso(campaign.start_date),
        "end_date": _optional_datetime_to_iso(campaign.end_date),
        "notes": campaign.notes,
        "metadata": _metadata_to_dict(campaign.metadata),
    }


def campaign_from_dict(data: Dict[str, Any]) -> Campaign:
    return _wrap_errors(
        "Campaign",
        data,
        lambda: Campaign(
            campaign_id=data["campaign_id"],
            name=data["name"],
            description=data["description"],
            status=CampaignStatus(data["status"]),
            territory=data["territory"],
            start_date=_optional_iso_to_datetime(data["start_date"]),
            end_date=_optional_iso_to_datetime(data["end_date"]),
            notes=data["notes"],
            metadata=_metadata_from_dict(data["metadata"], CampaignMetadata),
        ),
    )


# --- Lead ------------------------------------------------------------------


def lead_to_dict(lead: Lead) -> Dict[str, Any]:
    return {
        "lead_id": lead.lead_id,
        "company_id": lead.company_id,
        "contact_id": lead.contact_id,
        "campaign_id": lead.campaign_id,
        "status": lead.status.value,
        "territory": lead.territory,
        "source": lead.source,
        "next_touch_date": _optional_datetime_to_iso(lead.next_touch_date),
        "last_touch_date": _optional_datetime_to_iso(lead.last_touch_date),
        "dynamics_record_id": lead.dynamics_record_id,
        "sync_state": lead.sync_state.value,
        "notes": lead.notes,
        "metadata": _metadata_to_dict(lead.metadata),
    }


def lead_from_dict(data: Dict[str, Any]) -> Lead:
    return _wrap_errors(
        "Lead",
        data,
        lambda: Lead(
            lead_id=data["lead_id"],
            company_id=data["company_id"],
            contact_id=data["contact_id"],
            campaign_id=data["campaign_id"],
            status=LeadStatus(data["status"]),
            territory=data["territory"],
            source=data["source"],
            next_touch_date=_optional_iso_to_datetime(data["next_touch_date"]),
            last_touch_date=_optional_iso_to_datetime(data["last_touch_date"]),
            dynamics_record_id=data["dynamics_record_id"],
            sync_state=LeadSyncState(data["sync_state"]),
            notes=data["notes"],
            metadata=_metadata_from_dict(data["metadata"], LeadMetadata),
        ),
    )


# --- WorkItem ----------------------------------------------------------


def work_item_to_dict(work_item: WorkItem) -> Dict[str, Any]:
    return {
        "work_item_id": work_item.work_item_id,
        "lead_id": work_item.lead_id,
        "work_type": work_item.work_type.value,
        "status": work_item.status.value,
        "due_date": _optional_datetime_to_iso(work_item.due_date),
        "completed_at": _optional_datetime_to_iso(work_item.completed_at),
        "notes": work_item.notes,
        "metadata": _metadata_to_dict(work_item.metadata),
    }


def work_item_from_dict(data: Dict[str, Any]) -> WorkItem:
    return _wrap_errors(
        "WorkItem",
        data,
        lambda: WorkItem(
            work_item_id=data["work_item_id"],
            lead_id=data["lead_id"],
            work_type=WorkItemType(data["work_type"]),
            status=WorkItemStatus(data["status"]),
            due_date=_optional_iso_to_datetime(data["due_date"]),
            completed_at=_optional_iso_to_datetime(data["completed_at"]),
            notes=data["notes"],
            metadata=_metadata_from_dict(data["metadata"], WorkItemMetadata),
        ),
    )
