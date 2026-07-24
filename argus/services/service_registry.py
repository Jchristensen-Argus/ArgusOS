"""
In-memory implementation of the ArgusOS Service Registry.

Purpose:
    Provide the operating system's authoritative, in-process directory
    of services, per factory/packages/004_SERVICE_REGISTRY.md, so
    future components (Memory, Scheduler, Cortex, Atlas, Hermes,
    Applications, etc.) can discover services by name instead of
    depending on one another directly.

Responsibilities:
    - Register services, rejecting duplicate names.
    - Unregister services.
    - Resolve a registered service's instance by name.
    - Report whether a name is registered.
    - Enumerate every registered service, in registration order.
    - Fail explicitly (never silently) on invalid input.

Non-Responsibilities (explicitly out of scope for this package):
    Plugins, networking, persistence, dependency graphs, automatic
    startup, service health monitoring, event-driven lifecycle.

Dependencies:
    None beyond the standard library. The registry does not log,
    publish events, or call out to any other subsystem; this package's
    specification does not ask for it, unlike the Event Bus in
    Package 003.
"""

from typing import Dict, Tuple

from argus.services.exceptions import ServiceNotFoundError, ServiceRegistrationError
from argus.services.interfaces import IServiceRegistry
from argus.services.service_descriptor import ServiceDescriptor


class InMemoryServiceRegistry(IServiceRegistry):
    """
    In-memory, deterministic Service Registry.

    Purpose:
        Let ArgusOS subsystems discover services by name.

    Responsibilities:
        - register / unregister / resolve / contains / list_services,
          exactly as declared by IServiceRegistry.
        - Preserve registration order for list_services().

    Dependencies:
        None.
    """

    def __init__(self) -> None:
        self._services: Dict[str, ServiceDescriptor] = {}

    def register(self, descriptor: ServiceDescriptor) -> None:
        if not isinstance(descriptor, ServiceDescriptor):
            raise ServiceRegistrationError(
                f"Cannot register: {descriptor!r} is not a ServiceDescriptor."
            )
        if not descriptor.name:
            raise ServiceRegistrationError(
                "Cannot register: ServiceDescriptor.name must not be empty."
            )
        if descriptor.name in self._services:
            raise ServiceRegistrationError(
                f"A service is already registered under the name "
                f"{descriptor.name!r}."
            )
        self._services[descriptor.name] = descriptor

    def unregister(self, name: str) -> None:
        if name not in self._services:
            raise ServiceNotFoundError(
                f"Cannot unregister: no service is registered under {name!r}."
            )
        del self._services[name]

    def resolve(self, name: str) -> object:
        descriptor = self._services.get(name)
        if descriptor is None:
            raise ServiceNotFoundError(
                f"No service is registered under {name!r}."
            )
        return descriptor.instance

    def contains(self, name: str) -> bool:
        return name in self._services

    def list_services(self) -> Tuple[ServiceDescriptor, ...]:
        # dict preserves insertion order, so this is the registration
        # order, satisfying the "deterministic behavior" requirement.
        return tuple(self._services.values())
