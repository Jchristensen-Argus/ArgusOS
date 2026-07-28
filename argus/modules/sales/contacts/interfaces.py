"""
Interfaces for the Argus Sales OS Contacts package.

Purpose:
    Define IContactBuilder, the contract for a mutable, fluent Contact
    builder. Mirrors ICompanyBuilder: no new Core service is
    introduced, so IContactBuilder does not inherit IService.

Responsibilities:
    - IContactBuilder: the contract implemented by ContactBuilder.

Non-Responsibilities:
    - This module defines no concrete behavior - see builder.py.

Dependencies:
    argus.modules.sales.contacts.contact (Contact).
"""

from abc import ABC, abstractmethod
from typing import Any

from argus.modules.sales.contacts.contact import Contact


class IContactBuilder(ABC):
    """
    Contract for a mutable, fluent Contact builder.
    """

    @abstractmethod
    def with_company_id(self, company_id: str) -> "IContactBuilder":
        """Set this builder's company_id. Raises InvalidContactError
        if `company_id` is not a string."""

    @abstractmethod
    def with_first_name(self, first_name: str) -> "IContactBuilder":
        """Set this builder's first_name. Raises InvalidContactError
        if `first_name` is not a string."""

    @abstractmethod
    def with_last_name(self, last_name: str) -> "IContactBuilder":
        """Set this builder's last_name. Raises InvalidContactError if
        `last_name` is not a string."""

    @abstractmethod
    def with_email(self, email: str) -> "IContactBuilder":
        """Set this builder's email. Raises InvalidContactError if
        `email` is not a string."""

    @abstractmethod
    def with_phone(self, phone: str) -> "IContactBuilder":
        """Set this builder's phone. Raises InvalidContactError if
        `phone` is not a string."""

    @abstractmethod
    def with_title(self, title: str) -> "IContactBuilder":
        """Set this builder's title. Raises InvalidContactError if
        `title` is not a string."""

    @abstractmethod
    def with_notes(self, notes: str) -> "IContactBuilder":
        """Set this builder's notes. Raises InvalidContactError if
        `notes` is not a string."""

    @abstractmethod
    def with_metadata(self, key: str, value: Any) -> "IContactBuilder":
        """Set one arbitrary metadata key/value pair on the eventual
        ContactMetadata.extra mapping. Raises InvalidContactError if
        `key` is not a non-empty string."""

    @abstractmethod
    def build(self) -> Contact:
        """Construct and return a fresh, immutable Contact snapshot
        from this builder's current accumulated state."""
