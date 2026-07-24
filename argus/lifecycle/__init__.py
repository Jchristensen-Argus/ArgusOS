"""
ArgusOS Lifecycle package.

Purpose:
    Public entry point for the Service Lifecycle subsystem. Re-exports
    the symbols other modules need (LifecycleState, LifecycleManager,
    the IService contract, and the lifecycle exceptions) so callers
    can depend on `argus.lifecycle` rather than reaching into
    individual submodules.

Dependencies:
    None beyond the submodules it re-exports.
"""

from argus.lifecycle.exceptions import InvalidStateTransitionError, LifecycleError
from argus.lifecycle.interfaces import IService
from argus.lifecycle.lifecycle import LifecycleManager, LifecycleState

__all__ = [
    "IService",
    "LifecycleState",
    "LifecycleManager",
    "LifecycleError",
    "InvalidStateTransitionError",
]
