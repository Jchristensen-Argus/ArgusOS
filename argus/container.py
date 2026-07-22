"""
Dependency injection container for ArgusOS.

Purpose:
    Provide a simple, explicit registry for application services so that
    subsystems can be wired together at startup without hard-coded
    imports between engines, per design/specifications/INTERFACES.md.

Responsibilities:
    - Register a service instance under a stable name.
    - Resolve a previously registered service by name.
    - Report clearly when a requested service is not registered.

Non-Responsibilities:
    - The Container does not construct services. Construction happens in
      argus/bootstrap.py; the Container only stores and returns
      already-constructed instances.

Dependencies:
    None. The Container is foundational infrastructure.
"""

from typing import Any, Dict


class ServiceNotRegisteredError(Exception):
    """Raised when a requested service has not been registered with the container."""


class ServiceAlreadyRegisteredError(Exception):
    """Raised when attempting to register a service name that is already in use."""


class Container:
    """
    Minimal dependency injection container.

    The Container owns the lifetime of registered service instances and
    provides name-based lookup so subsystems can depend on interfaces
    rather than concrete implementations.
    """

    def __init__(self) -> None:
        self._services: Dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        """
        Register a service instance under a given name.

        Parameters:
            name: Unique identifier for the service (e.g. "configuration", "logger").
            service: The service instance to register.

        Raises:
            ServiceAlreadyRegisteredError: If a service is already registered
                under this name.
        """
        if name in self._services:
            raise ServiceAlreadyRegisteredError(
                f"Service '{name}' is already registered."
            )
        self._services[name] = service

    def resolve(self, name: str) -> Any:
        """
        Retrieve a previously registered service.

        Parameters:
            name: The identifier the service was registered under.

        Returns:
            The registered service instance.

        Raises:
            ServiceNotRegisteredError: If no service is registered under this name.
        """
        try:
            return self._services[name]
        except KeyError:
            raise ServiceNotRegisteredError(
                f"Service '{name}' has not been registered."
            ) from None

    def has(self, name: str) -> bool:
        """Return True if a service is registered under the given name."""
        return name in self._services
