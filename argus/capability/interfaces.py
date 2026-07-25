"""
Public interface contract for the ArgusOS Capability Registry.

Purpose:
    Define ICapabilityRegistry, the contract other modules depend on,
    per factory/packages/013_CAPABILITY_REGISTRY.md.

Architectural Note - Why ICapabilityRegistry Does NOT Inherit IService:
    Unlike Scheduler, IntentRouter, WorkflowEngine, ConversationManager,
    and IntentDispatcher (Packages 008-012), CapabilityRegistry has no
    genuine multi-phase behavior: register/unregister/get/
    find_by_intent_type/list_capabilities/contains are all fully usable
    the instant the registry is constructed, with no background
    thread, no connection to open or close, and nothing meaningful for
    start()/stop() to enable or disable. Per ADR-0002's proposed
    criterion ("adopt IService only when start()/stop() would do real,
    distinct work"), this is architecturally identical to Knowledge
    Service (Package 006) and Memory Service (Package 007), both of
    which deliberately did not adopt IService for the same reason -
    see design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md's
    Empirical Finding for this package. CapabilityRegistry is
    registered with the Lifecycle Manager as LifecycleState.REGISTERED
    only, exactly like Knowledge Service and Memory Service, not as a
    fully-lifecycled IService adopter.

Responsibilities:
    - ICapabilityRegistry: register / unregister / get /
      find_by_intent_type / list_capabilities / contains.

Non-Responsibilities:
    - This module implements no behavior; see
      argus.capability.registry.CapabilityRegistry.

Dependencies:
    argus.capability.capability (Capability), argus.intent.intent
    (IntentType).
"""

from abc import ABC, abstractmethod
from typing import Sequence

from argus.capability.capability import Capability
from argus.intent.intent import IntentType


class ICapabilityRegistry(ABC):
    """
    Metadata-only registry contract for everything ArgusOS knows how
    to do.

    Purpose:
        Let callers register, discover, and enumerate Capabilities
        without the registry itself executing anything - see this
        module's Architectural Note for why this interface is a plain
        ABC rather than an IService.
    """

    @abstractmethod
    def register(self, capability: Capability) -> None:
        """Register `capability`. Raises InvalidCapabilityError if
        capability is not a Capability instance, or has an empty id,
        empty name, empty intent_types, empty action_kind, or an
        action_kind of "workflow" with no workflow_id. Raises
        DuplicateCapabilityError if capability.id is already
        registered - call unregister() first to replace it."""

    @abstractmethod
    def unregister(self, capability_id: str) -> None:
        """Remove the Capability currently registered under
        capability_id. Raises InvalidCapabilityError if capability_id
        is not a string. Raises CapabilityNotFoundError if
        capability_id has no registered Capability."""

    @abstractmethod
    def get(self, capability_id: str) -> Capability:
        """Return the Capability registered under capability_id.
        Raises InvalidCapabilityError if capability_id is not a
        string. Raises CapabilityNotFoundError if capability_id has no
        registered Capability."""

    @abstractmethod
    def find_by_intent_type(self, intent_type: IntentType) -> Sequence[Capability]:
        """Return every registered Capability (enabled or disabled)
        whose intent_types includes intent_type, in registration
        order. Raises InvalidCapabilityError if intent_type is not an
        IntentType. A pure filter: applies no enabled/disabled policy
        and no selection between multiple matches - see
        argus.dispatcher.dispatcher.IntentDispatcher.resolve() for
        where that selection policy lives."""

    @abstractmethod
    def list_capabilities(self) -> Sequence[Capability]:
        """Return every registered Capability, in registration
        order."""

    @abstractmethod
    def contains(self, capability_id: str) -> bool:
        """Return True if capability_id is currently registered,
        False otherwise. Never raises for any input, including a
        non-string capability_id."""
