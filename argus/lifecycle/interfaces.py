"""
Public interface contract for ArgusOS services.

Purpose:
    Define the common lifecycle contract every ArgusOS service will
    implement, per factory/packages/005_SERVICE_LIFECYCLE.md, so the
    kernel can treat every service the same way regardless of what it
    does.

Responsibilities:
    - Declare initialize, start, stop, and status as the complete
      lifecycle surface of a service.

Non-Responsibilities:
    - This module implements nothing. No service in the current
      codebase (Configuration, the Logger, the Event Bus, the Service
      Registry, the Lifecycle Manager itself) implements IService yet;
      retrofitting them is out of scope for this package (see the
      Package 005 engineering notes).

Dependencies:
    argus.lifecycle.lifecycle (LifecycleState), for status()'s return
    type.
"""

from abc import ABC, abstractmethod

from argus.lifecycle.lifecycle import LifecycleState


class IService(ABC):
    """
    Common lifecycle contract for ArgusOS services.

    Purpose:
        Let every future ArgusOS service (Memory, Scheduler, Cortex,
        Atlas, Hermes, etc.) be initialized, started, stopped, and
        queried for status in exactly the same way.
    """

    @abstractmethod
    def initialize(self) -> None:
        """
        Prepare the service to run.

        Perform any setup that must happen before start(): validating
        configuration, acquiring resources, and so on. Must not begin
        the service's active work.
        """
        raise NotImplementedError

    @abstractmethod
    def start(self) -> None:
        """
        Begin the service's active work.

        Must only be called after initialize() has completed.
        """
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        """
        Stop the service's active work and release any resources
        acquired during initialize() or start().
        """
        raise NotImplementedError

    @abstractmethod
    def status(self) -> LifecycleState:
        """
        Report the service's current LifecycleState.
        """
        raise NotImplementedError
