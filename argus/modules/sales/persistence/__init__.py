"""
argus.modules.sales.persistence - Sales module session persistence
(Sprint 1, Slice 5).

Re-exports the public surface: SalesRepository,
DEFAULT_SALES_DATA_DIR, the session-orchestration functions
(import_and_persist, load_work_queue, save_work_queue), and this
package's own exceptions. See repository.py's module docstring for
the full persistence-boundary rationale.
"""

from argus.modules.sales.persistence.exceptions import SalesPersistenceError
from argus.modules.sales.persistence.repository import (
    DEFAULT_SALES_DATA_DIR,
    SalesRepository,
)
from argus.modules.sales.persistence.session import (
    import_and_persist,
    load_work_queue,
    save_work_queue,
)

__all__ = [
    "SalesRepository",
    "DEFAULT_SALES_DATA_DIR",
    "import_and_persist",
    "load_work_queue",
    "save_work_queue",
    "SalesPersistenceError",
]
