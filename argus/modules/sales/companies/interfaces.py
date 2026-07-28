"""
Interfaces for the Argus Sales OS Companies package.

Purpose:
    Define ICompanyBuilder, the contract for a mutable, fluent Company
    builder. Mirrors argus.modules.sales.leads.interfaces.ILeadBuilder:
    no new Core service is introduced, so ICompanyBuilder does not
    inherit IService.

Responsibilities:
    - ICompanyBuilder: the contract implemented by CompanyBuilder.

Non-Responsibilities:
    - This module defines no concrete behavior - see builder.py.

Dependencies:
    argus.modules.sales.companies.company (Company).
"""

from abc import ABC, abstractmethod
from typing import Any

from argus.modules.sales.companies.company import Company


class ICompanyBuilder(ABC):
    """
    Contract for a mutable, fluent Company builder.
    """

    @abstractmethod
    def with_name(self, name: str) -> "ICompanyBuilder":
        """Set this builder's name. A later call overwrites an
        earlier one. Raises InvalidCompanyError if `name` is not a
        non-empty string."""

    @abstractmethod
    def with_industry(self, industry: str) -> "ICompanyBuilder":
        """Set this builder's industry. A later call overwrites an
        earlier one. Raises InvalidCompanyError if `industry` is not a
        string."""

    @abstractmethod
    def with_website(self, website: str) -> "ICompanyBuilder":
        """Set this builder's website. A later call overwrites an
        earlier one. Raises InvalidCompanyError if `website` is not a
        string."""

    @abstractmethod
    def with_territory(self, territory: str) -> "ICompanyBuilder":
        """Set this builder's territory. A later call overwrites an
        earlier one. Raises InvalidCompanyError if `territory` is not
        a string."""

    @abstractmethod
    def with_notes(self, notes: str) -> "ICompanyBuilder":
        """Set this builder's notes. A later call overwrites an
        earlier one. Raises InvalidCompanyError if `notes` is not a
        string."""

    @abstractmethod
    def with_metadata(self, key: str, value: Any) -> "ICompanyBuilder":
        """Set one arbitrary metadata key/value pair on the eventual
        CompanyMetadata.extra mapping. Raises InvalidCompanyError if
        `key` is not a non-empty string."""

    @abstractmethod
    def build(self) -> Company:
        """Construct and return a fresh, immutable Company snapshot
        from this builder's current accumulated state."""
