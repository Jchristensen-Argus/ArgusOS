"""
The Contact value object for the Argus Sales OS Contacts package.

Purpose:
    Represent a single person (contact) at a Company, as an immutable
    value object, per ARGUS_SALES_OS_V1_ARCHITECTURE.md's canonical
    data models. Mirrors Company's own shape exactly: a frozen
    dataclass, every field defaulted so Contact() is always valid, no
    validation of its own beyond typing - see builder.py.

Company Is Referenced By Id, Not Embedded:
    Same discipline as Lead.company_id/Lead.contact_id - Contact holds
    `company_id` as a plain string, never a live Company instance or
    an import of argus.modules.sales.companies, keeping both packages
    free of a circular dependency and matching the "pure,
    dependency-free leaf" precedent set throughout this codebase.

Responsibilities:
    - Contact: hold identity (`contact_id`), a reference to its
      Company (`company_id`), name and reachability fields
      (`first_name`, `last_name`, `email`, `phone`, `title`),
      free-text `notes`, and descriptive ContactMetadata, as an
      immutable value object.

Non-Responsibilities:
    - Contact performs no reasoning, scheduling, or synchronization of
      any kind.
    - Contact does not reference any Lead - referencing runs the
      other direction (Lead.contact_id).

Dependencies:
    argus.modules.sales.contacts.metadata (ContactMetadata).
"""

import uuid
from dataclasses import dataclass, field

from argus.modules.sales.contacts.metadata import ContactMetadata


@dataclass(frozen=True)
class Contact:
    """
    An immutable record of one person at a Company. See the module
    docstring for the full field semantics.

    Fields:
        contact_id: Unique identifier for this Contact. Defaults to a
            fresh uuid4 string.
        company_id: The id of the Company this Contact belongs to.
            Defaults to an empty string (unassigned).
        first_name: The contact's first name. Defaults to an empty
            string.
        last_name: The contact's last name. Defaults to an empty
            string.
        email: The contact's email address. Defaults to an empty
            string.
        phone: The contact's phone number. Defaults to an empty
            string.
        title: The contact's job title. Defaults to an empty string.
        notes: Free-text notes. Defaults to an empty string.
        metadata: Descriptive bookkeeping about this Contact. Defaults
            to a fresh ContactMetadata.
    """

    contact_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    title: str = ""
    notes: str = ""
    metadata: ContactMetadata = field(default_factory=ContactMetadata)
