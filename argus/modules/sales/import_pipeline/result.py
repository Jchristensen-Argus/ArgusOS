"""
The ImportResult value object for the Argus Sales OS import pipeline.

Purpose:
    Summarize the outcome of one import run: what was parsed, what
    was created versus reused, which rows failed, and - as of Sprint 1
    Slice 5 - the actual entities involved, so a caller can persist
    them (see argus.modules.sales.persistence.session).

Not Given The Full Metadata Treatment, Deliberately:
    Unlike Lead/Company/Contact/Campaign/WorkItem, ImportResult has no
    dedicated *Metadata value object of its own. Those five are
    persistent domain entities with their own identity and lifecycle;
    ImportResult is a transient summary of a single run, discarded
    once read, the same shape as bootstrap()'s own Application return
    value - "every domain entity gets a Metadata companion" was never
    the rule; "every entity with its own identity and lifecycle does"
    is, and a one-off run summary has neither.

Asymmetry Between `companies`/`contacts`/`campaigns` And `leads` -
Read This Before Persisting:
    `companies`, `contacts`, and `campaigns` each hold that entity
    type's FULL current set - every pre-existing entity the Importer
    was seeded with (see importer.py's `existing_companies`/
    `existing_contacts`/`existing_campaigns` parameters), plus any
    newly created this run - because deduplication requires the
    Importer to hold the complete set in memory already. It is safe to
    pass these three sequences directly to
    SalesRepository.save_companies()/save_contacts()/save_campaigns(),
    which replace the entire stored collection.
    `leads`, by contrast, holds only the Leads created THIS run -
    there is no Lead-level deduplication (every row is a new Lead), so
    the Importer never sees or needs the previously-stored Lead
    collection. A caller must merge `leads` with whatever
    SalesRepository.load_leads() previously returned before calling
    save_leads() - passing `leads` alone to save_leads() would
    silently discard every previously-stored Lead. See
    persistence/session.py's import_and_persist(), which performs this
    merge correctly.

Responsibilities:
    - ImportResult: hold row/entity counts, the list of per-row
      failures, and the entities themselves from one import run, as an
      immutable value object.

Non-Responsibilities:
    - ImportResult performs no computation - it is populated by
      Importer.import_file() and read by the caller.
    - ImportResult does not persist anything itself - see
      persistence/session.py.

Dependencies:
    argus.modules.sales.companies (Company), .contacts (Contact),
    .campaigns (Campaign), .leads (Lead) - typing only.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Sequence, Tuple

if TYPE_CHECKING:
    from argus.modules.sales.campaigns.campaign import Campaign
    from argus.modules.sales.companies.company import Company
    from argus.modules.sales.contacts.contact import Contact
    from argus.modules.sales.leads.lead import Lead


@dataclass(frozen=True)
class ImportResult:
    """
    An immutable summary of one Lead Workspace import run.

    Fields:
        total_rows: How many data rows the source file contained.
        leads_created: How many Lead objects were created.
        companies_created: How many new Company objects were created.
        companies_reused: How many rows matched an already-seen
            Company within this same import run (by name) instead of
            creating a new one.
        contacts_created: How many new Contact objects were created.
        contacts_reused: How many rows matched an already-seen Contact
            within this same import run (by email) instead of
            creating a new one.
        campaigns_created: How many new Campaign objects were created.
        campaigns_reused: How many rows matched an already-seen
            Campaign within this same import run (by name) instead of
            creating a new one.
        errors: Human-readable messages for rows that failed to parse,
            in row order. A failed row is skipped, not fatal to the
            rest of the import - see importer.py's own module
            docstring.
        leads: The Lead objects created this run only. See the
            Asymmetry note above before persisting.
        companies: The FULL current Company set (seeded + created this
            run). See the Asymmetry note above before persisting.
        contacts: The FULL current Contact set (seeded + created this
            run). See the Asymmetry note above before persisting.
        campaigns: The FULL current Campaign set (seeded + created
            this run). See the Asymmetry note above before persisting.
    """

    total_rows: int = 0
    leads_created: int = 0
    companies_created: int = 0
    companies_reused: int = 0
    contacts_created: int = 0
    contacts_reused: int = 0
    campaigns_created: int = 0
    campaigns_reused: int = 0
    errors: Sequence[str] = field(default_factory=tuple)
    leads: Sequence["Lead"] = field(default_factory=tuple)
    companies: Sequence["Company"] = field(default_factory=tuple)
    contacts: Sequence["Contact"] = field(default_factory=tuple)
    campaigns: Sequence["Campaign"] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "errors", tuple(self.errors))
        object.__setattr__(self, "leads", tuple(self.leads))
        object.__setattr__(self, "companies", tuple(self.companies))
        object.__setattr__(self, "contacts", tuple(self.contacts))
        object.__setattr__(self, "campaigns", tuple(self.campaigns))

    @property
    def succeeded(self) -> int:
        """How many rows were successfully imported as a Lead."""
        return self.leads_created

    @property
    def failed(self) -> int:
        """How many rows failed to parse."""
        return len(self.errors)
