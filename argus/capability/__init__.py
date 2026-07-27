"""
Public re-exports for the ArgusOS Capability Registry / Capability
Framework package.

Purpose:
    Give callers a single, stable import surface
    (`from argus.capability import ...`) instead of reaching into
    individual submodules, matching the convention established by
    argus/workflow/__init__.py, argus/conversation/__init__.py, and
    argus/dispatcher/__init__.py. As of Package 033, also re-exports
    CapabilityMetadata, CapabilityBuilder, and ICapabilityBuilder.

Dependencies:
    argus.capability.capability, argus.capability.exceptions,
    argus.capability.interfaces, argus.capability.registry,
    argus.capability.metadata, argus.capability.builder.
"""

from argus.capability.builder import CapabilityBuilder
from argus.capability.capability import Capability
from argus.capability.exceptions import (
    CapabilityError,
    CapabilityNotFoundError,
    DuplicateCapabilityError,
    InvalidCapabilityError,
)
from argus.capability.interfaces import ICapabilityBuilder, ICapabilityRegistry
from argus.capability.metadata import CAPABILITY_METADATA_VERSION, CapabilityMetadata
from argus.capability.registry import CapabilityRegistry

__all__ = [
    "Capability",
    "CapabilityMetadata",
    "CAPABILITY_METADATA_VERSION",
    "ICapabilityBuilder",
    "CapabilityBuilder",
    "ICapabilityRegistry",
    "CapabilityRegistry",
    "CapabilityError",
    "InvalidCapabilityError",
    "DuplicateCapabilityError",
    "CapabilityNotFoundError",
]
