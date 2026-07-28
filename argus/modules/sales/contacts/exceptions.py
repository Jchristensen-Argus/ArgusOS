"""
Exceptions for the Argus Sales OS Contacts package.

Purpose:
    Define the error types argus.modules.sales.contacts itself can
    raise. Mirrors argus.modules.sales.companies.exceptions's shape.

Responsibilities:
    - ContactError: the base exception for this package.
    - InvalidContactError: raised by ContactBuilder's with_*()
      methods when given a malformed argument.

Non-Responsibilities:
    - This module performs no logic beyond defining exception types.

Dependencies:
    None.
"""


class ContactError(Exception):
    """Base exception for the argus.modules.sales.contacts package."""


class InvalidContactError(ContactError):
    """Raised when ContactBuilder's with_*() methods are given a
    malformed argument."""
