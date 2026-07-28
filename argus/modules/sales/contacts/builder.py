"""
The ContactBuilder for the Argus Sales OS Contacts package.

Purpose:
    Provide a mutable, fluent way to assemble a Contact's fields one
    at a time before producing a single immutable Contact snapshot.
    Directly mirrors argus.modules.sales.companies.builder.CompanyBuilder.

Validation Lives Here, Not On Contact:
    Every with_*() method below validates its argument before
    assigning it, raising InvalidContactError for malformed input.
    Unlike CompanyBuilder.with_name(), no field here is required
    non-empty - a Contact with every field at its empty-string default
    is a valid, if minimally useful, placeholder record (matching
    Lead's own "every field may default" posture, since a Contact
    parsed from a spreadsheet row may legitimately be missing a phone
    number or a title).

Responsibilities:
    - ContactBuilder: assign a Contact's fields one at a time, with
      per-field validation, and produce an immutable Contact snapshot
      on build().

Non-Responsibilities:
    - ContactBuilder performs no reasoning or synchronization of any
      kind - it only validates and assigns plain data.
    - ContactBuilder is not a service.

Dependencies:
    argus.modules.sales.contacts.contact (Contact),
    argus.modules.sales.contacts.metadata (ContactMetadata),
    argus.modules.sales.contacts.exceptions (InvalidContactError),
    argus.modules.sales.contacts.interfaces (IContactBuilder).
"""

from typing import Any, Dict

from argus.modules.sales.contacts.contact import Contact
from argus.modules.sales.contacts.exceptions import InvalidContactError
from argus.modules.sales.contacts.interfaces import IContactBuilder
from argus.modules.sales.contacts.metadata import ContactMetadata


def _require_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str):
        raise InvalidContactError(f"{label} must be a string, got {value!r}.")
    return value


class ContactBuilder(IContactBuilder):
    """
    A mutable, fluent builder for Contact. See the module docstring
    for the full assignment and validation semantics.
    """

    def __init__(self) -> None:
        self._company_id: str = ""
        self._first_name: str = ""
        self._last_name: str = ""
        self._email: str = ""
        self._phone: str = ""
        self._title: str = ""
        self._notes: str = ""
        self._metadata_extra: Dict[str, Any] = {}

    def with_company_id(self, company_id: str) -> "ContactBuilder":
        self._company_id = _require_string(company_id, label="company_id")
        return self

    def with_first_name(self, first_name: str) -> "ContactBuilder":
        self._first_name = _require_string(first_name, label="first_name")
        return self

    def with_last_name(self, last_name: str) -> "ContactBuilder":
        self._last_name = _require_string(last_name, label="last_name")
        return self

    def with_email(self, email: str) -> "ContactBuilder":
        self._email = _require_string(email, label="email")
        return self

    def with_phone(self, phone: str) -> "ContactBuilder":
        self._phone = _require_string(phone, label="phone")
        return self

    def with_title(self, title: str) -> "ContactBuilder":
        self._title = _require_string(title, label="title")
        return self

    def with_notes(self, notes: str) -> "ContactBuilder":
        self._notes = _require_string(notes, label="notes")
        return self

    def with_metadata(self, key: str, value: Any) -> "ContactBuilder":
        if not isinstance(key, str) or not key:
            raise InvalidContactError(
                f"metadata key must be a non-empty string, got {key!r}."
            )
        self._metadata_extra[key] = value
        return self

    def build(self) -> Contact:
        return Contact(
            company_id=self._company_id,
            first_name=self._first_name,
            last_name=self._last_name,
            email=self._email,
            phone=self._phone,
            title=self._title,
            notes=self._notes,
            metadata=ContactMetadata(extra=dict(self._metadata_extra)),
        )
