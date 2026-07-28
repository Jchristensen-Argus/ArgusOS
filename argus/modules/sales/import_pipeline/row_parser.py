"""
Row parsing for the Argus Sales OS import pipeline.

Purpose:
    Turn one raw spreadsheet row (a plain string-keyed mapping, the
    shape csv.DictReader produces) into a canonical-field-keyed dict,
    using a column mapping (column_mapping.py). Pure transformation -
    no entity construction, no deduplication, no Event Bus interaction
    happens here.

Why This Is Separate From importer.py:
    Parsing (turning a raw row into canonical fields) and orchestration
    (deciding whether a parsed row's Company/Contact already exists,
    constructing new entities, publishing events) are different
    concerns. Keeping them in separate modules means a future XLSX
    reader can reuse this exact parsing logic unchanged - only the
    thing that produces the raw row-as-mapping needs to differ between
    a CSV and an XLSX source.

Responsibilities:
    - parse_row(): extract canonical field values from one raw row
      using a column mapping, raising RowParseError for a
      structurally required field that's missing or blank.

Non-Responsibilities:
    - This module does not read a file, does not construct any Lead/
      Contact/Company/Campaign, and does not touch the Event Bus.

Dependencies:
    argus.modules.sales.import_pipeline.exceptions (RowParseError).
"""

from typing import Dict, Mapping

from argus.modules.sales.import_pipeline.exceptions import RowParseError

#: Fields a row cannot be usefully imported without. Every other field
#: in the column mapping is optional - a missing/blank value simply
#: becomes an empty string on the resulting entity, matching every
#: entity's own "every field defaults" posture (see leads/lead.py's
#: module docstring).
REQUIRED_CANONICAL_FIELDS = ("company_name",)


def parse_row(
    raw_row: Mapping[str, str],
    *,
    column_mapping: Mapping[str, str],
    row_number: int,
) -> Dict[str, str]:
    """
    Extract canonical field values from one raw spreadsheet row.

    Parameters:
        raw_row: The raw row, keyed by spreadsheet column name.
        column_mapping: canonical_field -> spreadsheet_column_name.
        row_number: The 1-indexed row number, for error messages only.

    Returns:
        A dict keyed by canonical field name (every key in
        column_mapping), with each value stripped of leading/trailing
        whitespace. A column present in column_mapping but absent from
        raw_row yields an empty string, not a KeyError - a spreadsheet
        missing an optional column entirely is not itself an error.

    Raises:
        RowParseError: If a field named in REQUIRED_CANONICAL_FIELDS
            is missing or blank after stripping.
    """
    parsed: Dict[str, str] = {}
    for canonical_field, column_name in column_mapping.items():
        raw_value = raw_row.get(column_name, "")
        parsed[canonical_field] = (raw_value or "").strip()

    for required_field in REQUIRED_CANONICAL_FIELDS:
        if not parsed.get(required_field):
            raise RowParseError(
                f"Row {row_number}: required field {required_field!r} "
                f"(column {column_mapping.get(required_field)!r}) is "
                f"missing or blank."
            )

    return parsed
