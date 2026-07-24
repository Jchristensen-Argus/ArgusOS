"""
ArgusOS Service Registry package.

Purpose:
    Public entry point for the Service Registry subsystem. Re-exports
    the symbols other modules need (ServiceDescriptor, the
    IServiceRegistry contract, the InMemoryServiceRegistry
    implementation, and the Service Registry exceptions) so callers
    can depend on `argus.services` rather than reaching into
    individual submodules.

    ServiceState was removed by the Package 005 architectural
    revision: runtime lifecycle state is now owned solely by
    argus.lifecycle.LifecycleManager. See
    argus/services/service_descriptor.py for details.

Dependencies:
    None beyond the submodules it re-exports.
"""

from argus.services.exceptions import ServiceNotFoundError, ServiceRegistrationError
from argus.services.interfaces import IServiceRegistry
from argus.services.service_descriptor import ServiceDescriptor
from argus.services.service_registry import InMemoryServiceRegistry

__all__ = [
    "ServiceDescriptor",
    "IServiceRegistry",
    "InMemoryServiceRegistry",
    "ServiceRegistrationError",
    "ServiceNotFoundError",
]
