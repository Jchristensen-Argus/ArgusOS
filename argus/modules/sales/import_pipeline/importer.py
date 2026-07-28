"""
The Importer for the Argus Sales OS Lead Workspace.

Purpose:
    Read a Lead Workspace CSV export and turn every row into
    canonical Lead/Contact/Company/Campaign objects, per
    ARGUS_SALES_OS_V1_ARCHITECTURE.md's Sprint 1 scope: "load the Lead
    Workspace spreadsheet, parse every lead into canonical Lead
    objects." CSV only for Sprint 1 - see the module docstring's
    Format Note below for why, and what an XLSX reader would need to
    add.

Format Note - CSV Now, XLSX Later, Same Parsing Underneath:
    The real Lead Workspace export is expected to be an Excel file,
    per the workflow described earlier in this engagement, not CSV.
    This importer reads CSV because it requires no new dependency
    (Python's stdlib csv module) and produces the exact same
    row-as-mapping shape XLSX parsing would (a dict keyed by column
    header) - row_parser.parse_row() already works against that shape
    regardless of source. Adding real XLSX support later means adding
    one new function that reads an .xlsx file and yields
    Dict[str, str] rows in that same shape; nothing in row_parser.py,
    column_mapping.py, or this module's own dedup/construction logic
    would need to change. Confirm the real file format before treating
    CSV-only as sufficient for production use.

Deduplication Now Spans Runs, If Seeded (Sprint 1, Slice 5):
    Company (by name, case-insensitive), Contact (by email,
    case-insensitive), and Campaign (by name, case-insensitive) are
    deduplicated against whatever this Importer was constructed with
    via `existing_companies`/`existing_contacts`/`existing_campaigns`,
    PLUS whatever this same call to import_file() has already seen.
    Importer itself still holds no persistent store and performs no
    I/O of its own - it stays exactly as testable as before, seeded or
    not. Loading the previous run's entities from disk and passing
    them in here is persistence/session.py's job (see
    import_and_persist()), not this class's. Constructing an Importer
    with no seed arguments (the original Slice 4 behavior) still
    dedups within-run only, unchanged.

A Failed Row Is Skipped, Not Fatal:
    A row that raises RowParseError is recorded in
    ImportResult.errors and the import continues with the next row -
    matching ordinary spreadsheet-import expectations (one malformed
    row from three hundred should not discard the other two hundred
    ninety-nine). This is a deliberate choice, not an oversight: an
    importer that aborts entirely on the first bad row would be far
    less useful to an actual salesperson working from a real,
    imperfect export.

Where Domain Events Are Published:
    Exactly the call site argus/modules/sales/events.py's own module
    docstring said didn't exist yet: for every successfully
    constructed Lead, import_file() calls publish_sales_event() with
    event_name="LeadImported" - if an event_bus is supplied. The
    event_bus parameter is optional specifically so this importer
    remains fully testable without a live Application (see this
    package's own test coverage) - matching Lead/Company/Contact/
    Campaign/WorkItem's own "verified via direct construction, no
    bootstrap() required" precedent from Slices 1-2.

Responsibilities:
    - Importer: read a CSV file, parse each row, deduplicate Company/
      Contact/Campaign within the run, construct Lead objects, publish
      LeadImported events, and return an ImportResult summary.

Non-Responsibilities:
    - Importer does not write to Dynamics, does not perform browser
      automation, and does not persist anything - Sprint 1's explicit
      scope excludes all three.
    - Importer does not decide work-queue ordering or filtering - that
      is the future work-queue module's responsibility.

Dependencies:
    argus.modules.sales.leads (Lead, LeadBuilder),
    argus.modules.sales.companies (Company, CompanyBuilder),
    argus.modules.sales.contacts (Contact, ContactBuilder),
    argus.modules.sales.campaigns (Campaign, CampaignBuilder),
    argus.modules.sales.events (publish_sales_event),
    argus.modules.sales.import_pipeline (column_mapping, row_parser,
    result, exceptions),
    argus.events (IEventBus) - typing only, optional at runtime.
"""

import csv
from typing import Dict, Iterable, List, Mapping, Optional

from argus.events.interfaces import IEventBus
from argus.modules.sales.campaigns import Campaign, CampaignBuilder
from argus.modules.sales.companies import Company, CompanyBuilder
from argus.modules.sales.contacts import Contact, ContactBuilder
from argus.modules.sales.events import publish_sales_event
from argus.modules.sales.import_pipeline.column_mapping import DEFAULT_COLUMN_MAPPING
from argus.modules.sales.import_pipeline.exceptions import RowParseError
from argus.modules.sales.import_pipeline.result import ImportResult
from argus.modules.sales.import_pipeline.row_parser import parse_row
from argus.modules.sales.leads import Lead, LeadBuilder


class Importer:
    """
    Reads a Lead Workspace CSV export and produces canonical Sales
    entities. See the module docstring for the full design rationale.
    """

    def __init__(
        self,
        *,
        column_mapping: Optional[Mapping[str, str]] = None,
        event_bus: Optional[IEventBus] = None,
        existing_companies: Optional[Iterable[Company]] = None,
        existing_contacts: Optional[Iterable[Contact]] = None,
        existing_campaigns: Optional[Iterable[Campaign]] = None,
    ) -> None:
        """
        Parameters:
            column_mapping: Overrides DEFAULT_COLUMN_MAPPING - pass
                this once a real export's actual column names are
                confirmed, per column_mapping.py's own Honesty Note.
            event_bus: If supplied, a LeadImported event is published
                for every successfully constructed Lead. If omitted,
                no events are published - the importer still works,
                for testing or offline use.
            existing_companies: Previously-stored Companies to
                dedup against, in addition to this run's own rows. See
                the module docstring's Deduplication note.
            existing_contacts: Previously-stored Contacts to dedup
                against. See the module docstring's Deduplication
                note.
            existing_campaigns: Previously-stored Campaigns to dedup
                against. See the module docstring's Deduplication
                note.
        """
        self._column_mapping = column_mapping or DEFAULT_COLUMN_MAPPING
        self._event_bus = event_bus
        self._seed_companies = list(existing_companies or ())
        self._seed_contacts = list(existing_contacts or ())
        self._seed_campaigns = list(existing_campaigns or ())

    def import_file(self, path: str) -> ImportResult:
        """
        Read the CSV file at `path` and import every row.

        Parameters:
            path: Filesystem path to the CSV file.

        Returns:
            An ImportResult summarizing what was created, reused, and
            failed.
        """
        companies_by_name: Dict[str, Company] = {
            company.name.lower(): company for company in self._seed_companies
        }
        contacts_by_email: Dict[str, Contact] = {
            contact.email.lower(): contact
            for contact in self._seed_contacts
            if contact.email
        }
        campaigns_by_name: Dict[str, Campaign] = {
            campaign.name.lower(): campaign for campaign in self._seed_campaigns
        }
        leads: List[Lead] = []
        errors: List[str] = []

        companies_created = companies_reused = 0
        contacts_created = contacts_reused = 0
        campaigns_created = campaigns_reused = 0
        total_rows = 0

        with open(path, "r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            for row_number, raw_row in enumerate(reader, start=1):
                total_rows += 1
                try:
                    fields = parse_row(
                        raw_row,
                        column_mapping=self._column_mapping,
                        row_number=row_number,
                    )
                except RowParseError as exc:
                    errors.append(str(exc))
                    continue

                company_key = fields["company_name"].lower()
                if company_key in companies_by_name:
                    company = companies_by_name[company_key]
                    companies_reused += 1
                else:
                    company = (
                        CompanyBuilder()
                        .with_name(fields["company_name"])
                        .with_industry(fields.get("company_industry", ""))
                        .with_website(fields.get("company_website", ""))
                        .with_territory(fields.get("territory", ""))
                        .build()
                    )
                    companies_by_name[company_key] = company
                    companies_created += 1

                contact = None
                contact_email = fields.get("contact_email", "")
                if contact_email:
                    contact_key = contact_email.lower()
                    if contact_key in contacts_by_email:
                        contact = contacts_by_email[contact_key]
                        contacts_reused += 1
                    else:
                        contact = (
                            ContactBuilder()
                            .with_company_id(company.company_id)
                            .with_first_name(fields.get("contact_first_name", ""))
                            .with_last_name(fields.get("contact_last_name", ""))
                            .with_email(contact_email)
                            .with_phone(fields.get("contact_phone", ""))
                            .with_title(fields.get("contact_title", ""))
                            .build()
                        )
                        contacts_by_email[contact_key] = contact
                        contacts_created += 1

                campaign = None
                campaign_name = fields.get("campaign_name", "")
                if campaign_name:
                    campaign_key = campaign_name.lower()
                    if campaign_key in campaigns_by_name:
                        campaign = campaigns_by_name[campaign_key]
                        campaigns_reused += 1
                    else:
                        campaign = CampaignBuilder().with_name(campaign_name).build()
                        campaigns_by_name[campaign_key] = campaign
                        campaigns_created += 1

                lead = (
                    LeadBuilder()
                    .with_company_id(company.company_id)
                    .with_contact_id(contact.contact_id if contact else "")
                    .with_campaign_id(campaign.campaign_id if campaign else "")
                    .with_territory(fields.get("territory", ""))
                    .with_source("lead_workspace_import")
                    .with_dynamics_record_id(fields.get("dynamics_record_id", ""))
                    .with_notes(fields.get("notes", ""))
                    .build()
                )
                leads.append(lead)

                if self._event_bus is not None:
                    publish_sales_event(
                        self._event_bus,
                        event_name="LeadImported",
                        entity_type="Lead",
                        entity_id=lead.lead_id,
                        extra={"row_number": row_number, "source_file": path},
                    )

        return ImportResult(
            total_rows=total_rows,
            leads_created=len(leads),
            companies_created=companies_created,
            companies_reused=companies_reused,
            contacts_created=contacts_created,
            contacts_reused=contacts_reused,
            campaigns_created=campaigns_created,
            campaigns_reused=campaigns_reused,
            errors=tuple(errors),
            leads=tuple(leads),
            companies=tuple(companies_by_name.values()),
            contacts=tuple(contacts_by_email.values()),
            campaigns=tuple(campaigns_by_name.values()),
        )
