"""
ArgusOS Memory Service package.

Purpose:
    Public entry point for the Memory Service subsystem. Re-exports
    the symbols other modules need (MemoryRecord, the
    IMemoryService/IMemoryStorage contracts, the
    MemoryService/JSONMemoryStorage implementations, and the memory
    exceptions) so callers can depend on `argus.memory` rather than
    reaching into individual submodules.

Dependencies:
    None beyond the submodules it re-exports.
"""

from argus.memory.exceptions import (
    DuplicateMemoryError,
    MemoryNotFoundError,
    MemoryServiceError,
)
from argus.memory.interfaces import IMemoryService, IMemoryStorage
from argus.memory.memory_record import MemoryRecord
from argus.memory.memory_service import MemoryService
from argus.memory.storage import JSONMemoryStorage

__all__ = [
    "MemoryRecord",
    "IMemoryService",
    "IMemoryStorage",
    "MemoryService",
    "JSONMemoryStorage",
    "MemoryServiceError",
    "MemoryNotFoundError",
    "DuplicateMemoryError",
]
