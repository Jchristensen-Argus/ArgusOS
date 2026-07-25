"""
Public re-exports for the ArgusOS Capability Registry package.

Purpose:
    Give callers a single, stable import surface
    (`from argus.capability import ...`) instead of reaching into
    individual submodules, matching the convention established by
    argus/workflow/__init__.py, argus/conversation/__init__.py, and
    argus/dispatcher/__init__.py.

Dependencies:
    argus.capability.capability, argus.capability.exceptions,
    argus.capability.interfaces, argus.capability.registry.
"""

from argus.capability.capability import Capability
from argus.capability.exceptions import (
    CapabilityError,
    CapabilityNotFoundError,
    DuplicateCapabilityError,
    InvalidCapabilityError,
)
from argus.capability.interfaces import ICapabilityRegistry
from argus.capability.registry import CapabilityRegistry

__all__ = [
    "Capability",
    "ICapabilityRegistry",
    "CapabilityRegistry",
    "CapabilityError",
    "InvalidCapabilityError",
    "DuplicateCapabilityError",
    "CapabilityNotFoundError",
]
