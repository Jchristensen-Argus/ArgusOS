"""
Public interface contracts for the ArgusOS Capability Registry /
Capability Framework.

Purpose:
    Define ICapabilityRegistry, the contract other modules depend on,
    per factory/packages/013_CAPABILITY_REGISTRY.md, and (as of
    Package 033) ICapabilityBuilder, the contract for a mutable,
    fluent Capability builder, per
    factory/packages/033_CAPABILITY_FRAMEWORK.md.

Architectural Note - ICapabilityBuilder Does Not Inherit IService
(Package 033):
    Exactly mirroring ICognitiveContextBuilder (022),
    IPlanningSessionBuilder (023), ITraceBuilder (028), ITaskBuilder
    (029), IRelationshipBuilder (031), and IExecutionResultBuilder
    (032), none of which inherit IService either - a builder has no
    meaningful start/stop lifecycle of its own; it is a short-lived,
    per-use accumulator.

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
    - ICapabilityRegistry: register / unregister / get / get_by_name
      (Package 033) / find_by_intent_type / list_capabilities /
      contains.
    - ICapabilityBuilder (Package 033): the contract implemented by
      CapabilityBuilder.

Non-Responsibilities:
    - This module implements no behavior; see
      argus.capability.registry.CapabilityRegistry and (as of Package
      033) argus.capability.builder.CapabilityBuilder.

Dependencies:
    argus.capability.capability (Capability), argus.intent.intent
    (IntentType), argus.lifecycle.interfaces (IService) - referenced
    only in this module's own Architectural Note, not inherited by
    ICapabilityBuilder.
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
        registered, or (Package 033) if capability.name is already
        registered under a different id - call unregister() first to
        replace either."""

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
    def get_by_name(self, name: str) -> Capability:
        """Return the Capability currently registered under `name`
        (Package 033 - "lookup by name"). Raises
        InvalidCapabilityError if name is not a string. Raises
        CapabilityNotFoundError if no currently-registered Capability
        has that name."""

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


class ICapabilityBuilder(ABC):
    """
    Contract for a mutable, fluent Capability builder (Package 033).
    See this module's docstring for why ICapabilityBuilder does not
    inherit IService.
    """

    @abstractmethod
    def with_id(self, id: str) -> "ICapabilityBuilder":
        """Set this builder's id. A later call overwrites an earlier
        one - the last call before build() wins. When never called,
        build() lets Capability's own default_factory generate a
        fresh id. Raises InvalidCapabilityError if `id` is not a
        non-empty string."""

    @abstractmethod
    def with_name(self, name: str) -> "ICapabilityBuilder":
        """Set this builder's name. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidCapabilityError if `name` is not a non-empty string."""

    @abstractmethod
    def with_description(self, description: str) -> "ICapabilityBuilder":
        """Set this builder's description. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidCapabilityError if `description` is not a string."""

    @abstractmethod
    def with_intent_type(self, intent_type: IntentType) -> "ICapabilityBuilder":
        """Validate and append one IntentType to this builder's
        intent_types, in call order. Accumulates across multiple
        calls. Raises InvalidCapabilityError if `intent_type` is not
        an IntentType instance."""

    @abstractmethod
    def with_intent_types(self, intent_types: Sequence[IntentType]) -> "ICapabilityBuilder":
        """Validate and append each item of `intent_types` to this
        builder's intent_types, in order, by delegating to
        with_intent_type() once per item. Raises
        InvalidCapabilityError if `intent_types` is not a list or
        tuple, or if any item is not an IntentType instance."""

    @abstractmethod
    def clear_intent_types(self) -> "ICapabilityBuilder":
        """Reset this builder's accumulated intent_types to empty."""

    @abstractmethod
    def with_action_kind(self, action_kind: str) -> "ICapabilityBuilder":
        """Set this builder's action_kind. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidCapabilityError if `action_kind` is not a non-empty
        string."""

    @abstractmethod
    def with_workflow_id(self, workflow_id) -> "ICapabilityBuilder":
        """Set this builder's workflow_id. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidCapabilityError if `workflow_id` is neither a string
        nor None."""

    @abstractmethod
    def with_enabled(self, enabled: bool) -> "ICapabilityBuilder":
        """Set this builder's enabled flag. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidCapabilityError if `enabled` is not a bool."""

    @abstractmethod
    def with_version(self, version: str) -> "ICapabilityBuilder":
        """Set this builder's version. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidCapabilityError if `version` is not a non-empty
        string."""

    @abstractmethod
    def with_metadata(self, key: str, value) -> "ICapabilityBuilder":
        """Set one arbitrary metadata key/value pair on the eventual
        CapabilityMetadata.extra mapping (Package 033) - not
        Capability's own pre-existing (013) `metadata` field, which
        this builder does not populate. Accumulates across multiple
        calls; the same key overwrites - last call wins. Raises
        InvalidCapabilityError if `key` is not a non-empty string."""

    @abstractmethod
    def build(self) -> Capability:
        """Construct and return a fresh, immutable Capability snapshot
        from this builder's current accumulated state."""
