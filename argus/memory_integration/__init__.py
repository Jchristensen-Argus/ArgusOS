"""
Public re-exports for the ArgusOS Memory Integration package.

Purpose:
    Give callers a single, stable import surface
    (`from argus.memory_integration import ...`) instead of reaching
    into individual submodules, matching the convention established
    by argus/knowledge_graph/__init__.py, argus/connectors/__init__.py,
    argus/runtime/__init__.py, argus/planner/__init__.py, and
    argus/plugins/__init__.py.

Dependencies:
    argus.memory_integration.exceptions,
    argus.memory_integration.integration,
    argus.memory_integration.interfaces, argus.memory_integration.mapper.
"""

from argus.memory_integration.exceptions import (
    InvalidMemoryIntegrationStateError,
    InvalidMemoryRecordError,
    MemoryIntegrationError,
    MemoryMappingError,
    MemoryNotSynchronizedError,
)
from argus.memory_integration.integration import MemoryIntegration
from argus.memory_integration.interfaces import IMemoryIntegration
from argus.memory_integration.mapper import MemoryMapper

__all__ = [
    "IMemoryIntegration",
    "MemoryIntegration",
    "MemoryMapper",
    "MemoryIntegrationError",
    "InvalidMemoryRecordError",
    "MemoryMappingError",
    "MemoryNotSynchronizedError",
    "InvalidMemoryIntegrationStateError",
]
