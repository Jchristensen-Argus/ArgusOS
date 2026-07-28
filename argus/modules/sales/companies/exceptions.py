"""
Exceptions for the Argus Sales OS Companies package.

Purpose:
    Define the error types argus.modules.sales.companies itself can
    raise. Mirrors argus.modules.sales.leads.exceptions's shape.

Responsibilities:
    - CompanyError: the base exception for this package.
    - InvalidCompanyError: raised by CompanyBuilder's with_*() methods
      when given a malformed argument.

Non-Responsibilities:
    - This module performs no logic beyond defining exception types.

Dependencies:
    None.
"""


class CompanyError(Exception):
    """Base exception for the argus.modules.sales.companies package."""


class InvalidCompanyError(CompanyError):
    """Raised when CompanyBuilder's with_*() methods are given a
    malformed argument."""
