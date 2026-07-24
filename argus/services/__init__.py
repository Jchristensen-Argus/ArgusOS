"""
ArgusOS Service Registry package.

Purpose:
    Public entry point for the Service Registry subsystem. Re-exports
    the symbols other modules need (ServiceDescriptor, ServiceState,
    the IServiceRegistry contract, the InMemoryServiceRegistry
    implementation, and the Service Registry exceptions) so callers
    can depend on `argus.services` rather than reaching into
    individual submodules.

Dependencies:
    None beyond the submodules it re-exports.
"""

from argus.services.exceptions import ServiceNotFoundError, ServiceRegistrationError
from argus.services.interfaces import IServiceRegistry
from argus.services.service_descriptor import ServiceDescriptor, ServiceState
from argus.services.service_registry import InMemoryServiceRegistry

__all__ = [
    "ServiceDescriptor",
    "ServiceState",
    "IServiceRegistry",
    "InMemoryServiceRegistry",
    "ServiceRegistrationError",
    "ServiceNotFoundError",
]
