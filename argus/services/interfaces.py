"""
Public interface contract for the ArgusOS Service Registry.

Purpose:
    Define the Service Registry's public contract independently of any
    concrete implementation, per design/specifications/INTERFACES.md's
    "no subsystem may bypass another engine's published interface" and
    the "interfaces before implementations" principle established in
    Package 003.

    Other subsystems should depend on IServiceRegistry, not on
    InMemoryServiceRegistry, so the implementation can change without
    affecting callers.

Responsibilities:
    - Declare register, unregister, resolve, contains, and
      list_services as the complete public surface of a service
      registry.

Non-Responsibilities:
    - This module implements nothing.

Dependencies:
    argus.services.service_descriptor (ServiceDescriptor).
"""

from abc import ABC, abstractmethod
from typing import Any, Sequence

from argus.services.service_descriptor import ServiceDescriptor


class IServiceRegistry(ABC):
    """
    Authoritative directory of services contract for ArgusOS.

    Purpose:
        Let subsystems discover and use one another's services by
        name, without depending on one another directly.
    """

    @abstractmethod
    def register(self, descriptor: ServiceDescriptor) -> None:
        """
        Register a service.

        Parameters:
            descriptor: The ServiceDescriptor to register.

        Raises:
            ServiceRegistrationError: If the descriptor is invalid, or
                a service is already registered under
                `descriptor.name`.
        """
        raise NotImplementedError

    @abstractmethod
    def unregister(self, name: str) -> None:
        """
        Remove a previously registered service.

        Parameters:
            name: The name the service was registered under.

        Raises:
            ServiceNotFoundError: If no service is registered under
                this name.
        """
        raise NotImplementedError

    @abstractmethod
    def resolve(self, name: str) -> Any:
        """
        Retrieve a registered service's instance.

        Parameters:
            name: The name the service was registered under.

        Returns:
            The registered service instance (`ServiceDescriptor.instance`).

        Raises:
            ServiceNotFoundError: If no service is registered under
                this name.
        """
        raise NotImplementedError

    @abstractmethod
    def contains(self, name: str) -> bool:
        """
        Report whether a service is currently registered.

        Parameters:
            name: The service name to check.

        Returns:
            True if a service is registered under this name.
        """
        raise NotImplementedError

    @abstractmethod
    def list_services(self) -> Sequence[ServiceDescriptor]:
        """
        List every currently registered service.

        Returns:
            The registered ServiceDescriptors, in registration order.
        """
        raise NotImplementedError
