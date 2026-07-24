"""
ServiceDescriptor for the ArgusOS Service Registry.

Purpose:
    Represent everything the Service Registry knows about one
    registered service: its name, the running instance, the interface
    it fulfills, its version, and free-form metadata, per
    factory/packages/004_SERVICE_REGISTRY.md.

Responsibilities:
    - Define ServiceDescriptor, an immutable record combining a
      service's identity and descriptive data.

Non-Responsibilities:
    - ServiceDescriptor contains no business logic: it does not
      register, resolve, or validate itself.
    - ServiceDescriptor does not track runtime lifecycle state. That
      was originally modeled here as a `state: ServiceState` field
      (Package 004), but architecture review found this duplicated
      the Lifecycle Manager's LifecycleState (Package 005) as a second,
      unsynchronized source of truth for the same concept. Per the
      Package 005 architectural revision, the Lifecycle Manager
      (argus.lifecycle.LifecycleManager) is now the sole owner of
      runtime lifecycle state; ServiceDescriptor is purely descriptive
      data and never represents a point-in-time runtime state.

Dependencies:
    None (standard library only).
"""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


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
        - Store name, instance, interface, version, and metadata.
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
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        # Frozen dataclasses require object.__setattr__ during
        # __post_init__. This makes the metadata mapping itself
        # read-only, not just the attribute reference, matching the
        # immutability guarantee established for Event in Package 003.
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
