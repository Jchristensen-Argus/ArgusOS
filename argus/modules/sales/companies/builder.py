"""
The CompanyBuilder for the Argus Sales OS Companies package.

Purpose:
    Provide a mutable, fluent way to assemble a Company's fields one
    at a time before producing a single immutable Company snapshot.
    Directly mirrors argus.modules.sales.leads.builder.LeadBuilder.

Validation Lives Here, Not On Company:
    See company.py's own module docstring - Company performs no
    validation of its own; every with_*() method below validates its
    argument before assigning it, raising InvalidCompanyError for
    malformed input.

`name` Is Required Non-Empty, Every Other Field Is Not:
    Unlike Lead (where every field, including identifying ones, may
    be left at its empty-string default because a Lead is meaningless
    without a Company/Contact reference set later), a Company with no
    `name` is not a usable record on its own - with_name() therefore
    rejects an empty string, mirroring TaskBuilder.with_name()'s own
    "non-empty string required" rule for Task's own primary label.

Responsibilities:
    - CompanyBuilder: assign a Company's fields one at a time, with
      per-field validation, and produce an immutable Company snapshot
      on build().

Non-Responsibilities:
    - CompanyBuilder performs no reasoning or synchronization of any
      kind - it only validates and assigns plain data.
    - CompanyBuilder is not a service.

Dependencies:
    argus.modules.sales.companies.company (Company),
    argus.modules.sales.companies.metadata (CompanyMetadata),
    argus.modules.sales.companies.exceptions (InvalidCompanyError),
    argus.modules.sales.companies.interfaces (ICompanyBuilder).
"""

from typing import Any, Dict

from argus.modules.sales.companies.company import Company
from argus.modules.sales.companies.exceptions import InvalidCompanyError
from argus.modules.sales.companies.interfaces import ICompanyBuilder
from argus.modules.sales.companies.metadata import CompanyMetadata


def _require_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str):
        raise InvalidCompanyError(f"{label} must be a string, got {value!r}.")
    return value


class CompanyBuilder(ICompanyBuilder):
    """
    A mutable, fluent builder for Company. See the module docstring
    for the full assignment and validation semantics.
    """

    def __init__(self) -> None:
        self._name: str = ""
        self._industry: str = ""
        self._website: str = ""
        self._territory: str = ""
        self._notes: str = ""
        self._metadata_extra: Dict[str, Any] = {}

    def with_name(self, name: str) -> "CompanyBuilder":
        if not isinstance(name, str) or not name:
            raise InvalidCompanyError(
                f"name must be a non-empty string, got {name!r}."
            )
        self._name = name
        return self

    def with_industry(self, industry: str) -> "CompanyBuilder":
        self._industry = _require_string(industry, label="industry")
        return self

    def with_website(self, website: str) -> "CompanyBuilder":
        self._website = _require_string(website, label="website")
        return self

    def with_territory(self, territory: str) -> "CompanyBuilder":
        self._territory = _require_string(territory, label="territory")
        return self

    def with_notes(self, notes: str) -> "CompanyBuilder":
        self._notes = _require_string(notes, label="notes")
        return self

    def with_metadata(self, key: str, value: Any) -> "CompanyBuilder":
        if not isinstance(key, str) or not key:
            raise InvalidCompanyError(
                f"metadata key must be a non-empty string, got {key!r}."
            )
        self._metadata_extra[key] = value
        return self

    def build(self) -> Company:
        return Company(
            name=self._name,
            industry=self._industry,
            website=self._website,
            territory=self._territory,
            notes=self._notes,
            metadata=CompanyMetadata(extra=dict(self._metadata_extra)),
        )
