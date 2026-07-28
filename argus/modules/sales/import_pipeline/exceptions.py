"""
Exceptions for the Argus Sales OS import pipeline package.

Purpose:
    Define the error types argus.modules.sales.import_pipeline itself
    can raise.

Responsibilities:
    - ImportError_: the base exception for this package. Named with a
      trailing underscore to avoid shadowing the Python builtin
      ImportError, which this package's own row-parsing failures are
      conceptually unrelated to.
    - RowParseError: raised when a single spreadsheet row cannot be
      parsed into canonical field values.

Non-Responsibilities:
    - This module performs no logic beyond defining exception types.

Dependencies:
    None.
"""


class ImportError_(Exception):
    """Base exception for the argus.modules.sales.import_pipeline
    package. Named with a trailing underscore to avoid shadowing the
    builtin ImportError."""


class RowParseError(ImportError_):
    """Raised when a single spreadsheet row cannot be parsed into
    canonical field values - carries the 1-indexed row number and the
    underlying reason."""
