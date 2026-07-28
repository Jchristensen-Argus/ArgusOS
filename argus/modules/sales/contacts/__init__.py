"""
argus.modules.sales.contacts - The Contacts domain model (Sprint 1,
Slice 2).

Re-exports the public surface: Contact, ContactMetadata, the mutable
builder (ContactBuilder) and its interface (IContactBuilder), and this
package's own exceptions. See ARGUS_SALES_OS_V1_ARCHITECTURE.md for
the full architectural rationale.
"""

from argus.modules.sales.contacts.builder import ContactBuilder
from argus.modules.sales.contacts.contact import Contact
from argus.modules.sales.contacts.exceptions import (
    ContactError,
    InvalidContactError,
)
from argus.modules.sales.contacts.interfaces import IContactBuilder
from argus.modules.sales.contacts.metadata import (
    CONTACT_METADATA_VERSION,
    ContactMetadata,
)

__all__ = [
    "Contact",
    "ContactMetadata",
    "CONTACT_METADATA_VERSION",
    "ContactBuilder",
    "IContactBuilder",
    "ContactError",
    "InvalidContactError",
]
