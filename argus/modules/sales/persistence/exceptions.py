"""
Exceptions for the Argus Sales OS persistence package.

Purpose:
    Define the error types argus.modules.sales.persistence itself can
    raise. Mirrors argus.memory's and argus.knowledge's own storage
    exception shape (MemoryServiceError, KnowledgeError): one error
    type covering both read (malformed/corrupt file) and write
    (filesystem) failures, since callers handle both the same way -
    surface the failure, do not silently drop data.

Responsibilities:
    - SalesPersistenceError: the single exception this package raises,
      for both load and save failures.

Non-Responsibilities:
    - This module performs no logic beyond defining an exception type.

Dependencies:
    None.
"""


class SalesPersistenceError(Exception):
    """Raised when the Sales module's persistence layer fails to load
    or save a stored collection - a corrupt/malformed file, or a
    filesystem failure during a write."""
