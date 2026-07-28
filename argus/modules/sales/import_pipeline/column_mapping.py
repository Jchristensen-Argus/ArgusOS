"""
Column mapping for the Argus Sales OS Lead Workspace importer.

Purpose:
    Define which spreadsheet column names map to which canonical
    entity fields, per ARGUS_SALES_OS_V1_ARCHITECTURE.md's Sprint 1
    scope: "load the Lead Workspace spreadsheet, parse every lead into
    canonical Lead objects."

Honesty Note - This Mapping Is a Best Guess, Not a Confirmed Fact:
    No real Lead Workspace spreadsheet export (from Dynamics or
    ZoomInfo) has been provided to build this against. The column
    names below are a reasonable default based on the workflow
    described earlier in this engagement (ZoomInfo -> Dynamics ->
    manual review/approval -> Excel Lead Workspace), not a verified
    fact about the real export format. This is why the mapping is a
    plain, overridable dict rather than hardcoded into the parser
    itself - a caller with a real export in hand can pass their own
    DEFAULT_COLUMN_MAPPING override to Importer without touching this
    package's code. Confirm against a real sample file before treating
    the defaults below as production-accurate.

Responsibilities:
    - DEFAULT_COLUMN_MAPPING: the default spreadsheet-column-name ->
      canonical-field-name mapping.

Non-Responsibilities:
    - This module performs no parsing itself - see row_parser.py.

Dependencies:
    None.
"""

from types import MappingProxyType

#: Canonical field name -> the spreadsheet column name expected to
#: hold it. Overridable per-import via Importer's own constructor -
#: see importer.py.
DEFAULT_COLUMN_MAPPING = MappingProxyType(
    {
        "company_name": "Company Name",
        "company_industry": "Industry",
        "company_website": "Website",
        "contact_first_name": "First Name",
        "contact_last_name": "Last Name",
        "contact_email": "Email",
        "contact_phone": "Phone",
        "contact_title": "Title",
        "territory": "Territory",
        "campaign_name": "Campaign",
        "dynamics_record_id": "Dynamics ID",
        "notes": "Notes",
    }
)
