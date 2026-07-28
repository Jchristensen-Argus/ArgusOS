"""
argus.modules.sales.companies - The Companies domain model (Sprint 1,
Slice 2).

Re-exports the public surface: Company, CompanyMetadata, the mutable
builder (CompanyBuilder) and its interface (ICompanyBuilder), and this
package's own exceptions. See ARGUS_SALES_OS_V1_ARCHITECTURE.md for
the full architectural rationale.
"""

from argus.modules.sales.companies.builder import CompanyBuilder
from argus.modules.sales.companies.company import Company
from argus.modules.sales.companies.exceptions import (
    CompanyError,
    InvalidCompanyError,
)
from argus.modules.sales.companies.interfaces import ICompanyBuilder
from argus.modules.sales.companies.metadata import (
    COMPANY_METADATA_VERSION,
    CompanyMetadata,
)

__all__ = [
    "Company",
    "CompanyMetadata",
    "COMPANY_METADATA_VERSION",
    "CompanyBuilder",
    "ICompanyBuilder",
    "CompanyError",
    "InvalidCompanyError",
]
