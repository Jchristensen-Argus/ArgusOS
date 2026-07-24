"""
ServiceDescriptor and ServiceState for the ArgusOS Service Registry.

Purpose:
    Represent everything the Service Registry knows about one
    registered service: its name, the running instance, the interface
    it fulfills, its version, its lifecycle state, and free-form
    metadata, per factory/packages/004_SERVICE_REGISTRY.md.

Responsibilities:
    - Define ServiceState, the closed set of lifecycle states a
      registered service may be recorded as.
    - Define ServiceDescriptor, an immutable record combining a
      service's identity and descriptive data.

Non-Responsibilities:
    - ServiceDescriptor contains no business logic: it does not
      register, resolve, validate itself, or transition its own
      state. It also does not transition ServiceState automatically;
      this package does not implement service health monitoring or
      event-driven lifecycle (see factory/packages/004_SERVICE_REGISTRY.md
      Non-Goals). All of that belongs to, or is deferred beyond, the
      Service Registry.

Dependencies:
    None (standard library only).
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from types import MappingProxyType
from typing import Any, Mapping


class ServiceState(Enum):
    """The lifecycle state a service is recorded as by the Service
    Registry. The registry does not transition a service's state on
    its own (no automatic startup, no health monitoring); a state is
    simply the value carried by the ServiceDescriptor at registration
    time."""

    REGISTERED = auto()
    ACTIVE = auto()
    STOPPED = auto()


@dataclass(frozen=True)
class ServiceDescriptor:
    """
    An immutable record describing one service known to the Service
    Registry.

    Purpose:
        Carry a service's identity and descriptive data through the
        registry without exposing any way to mutate it after
        registration.

    Responsibilities:
        - Store name, instance, interface, version, state, and
          metadata.
        - Default `metadata` to an immutable empty mapping, and make
          any caller-supplied metadata immutable too, so a holder of a
          ServiceDescriptor can never mutate registry-held state
          through it.

    Dependencies:
        None.
    """

    name: str
    instance: Any
    interface: type
    version: str
    state: ServiceState
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        # Frozen dataclasses require object.__setattr__ during
        # __post_init__. This makes the metadata mapping itself
        # read-only, not just the attribute reference, matching the
        # immutability guarantee established for Event in Package 003.
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
