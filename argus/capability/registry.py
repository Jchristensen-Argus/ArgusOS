"""
CapabilityRegistry: in-memory, metadata-only implementation of
ICapabilityRegistry for the ArgusOS Capability Registry.

Purpose:
    Implement ICapabilityRegistry: store, validate, and let callers
    discover Capability metadata, per
    factory/packages/013_CAPABILITY_REGISTRY.md. The registry performs
    NO execution - it never constructs, obtains, or calls an Action,
    and never touches IWorkflowEngine or any other execution backend.

Responsibilities:
    - register / unregister / get / find_by_intent_type /
      list_capabilities / contains: an in-memory registry of
      Capability objects, keyed by id. All six methods are always
      available - CapabilityRegistry is not an IService adopter (see
      argus/capability/interfaces.py's Architectural Note), so there
      is no lifecycle state to gate any of them on.
    - register() validates a Capability's fields before accepting it
      (non-empty id/name/intent_types/action_kind, and a workflow_id
      when action_kind is "workflow") - the one piece of business
      logic this module contains, and it is validation, not
      execution, matching the precedent set by
      WorkflowEngine.register_workflow()'s own inline validation
      (Package 010).
    - Publishes CapabilityRegistered on every successful register()
      and CapabilityUnregistered on every successful unregister(),
      mirroring KnowledgeService's KNOWLEDGE_CREATED/KNOWLEDGE_DELETED
      precedent (Package 006) for a metadata CRUD store.

Non-Responsibilities:
    - CapabilityRegistry never selects "the" Capability for a given
      IntentType when multiple match, and never filters by the
      `enabled` flag - find_by_intent_type() returns every match,
      enabled or not. That selection policy belongs to whoever
      resolves a Capability into something to execute (IntentDispatcher
      in Version 1), not to the registry - see this module's own
      Purpose and argus/dispatcher/dispatcher.py's resolve().
    - No AI, no LLM, no networking, no persistence - Capabilities are
      held only in memory, exactly like WorkflowEngine's Workflows.

Dependencies:
    argus.capability (Capability, ICapabilityRegistry, and the
    capability exceptions), argus.events (Event, EventType, IEventBus),
    argus.intent.intent (IntentType).
"""

from typing import Dict, List, Sequence

from argus.capability.capability import Capability
from argus.capability.exceptions import (
    CapabilityNotFoundError,
    DuplicateCapabilityError,
    InvalidCapabilityError,
)
from argus.capability.interfaces import ICapabilityRegistry
from argus.events.event import Event
from argus.events.event_types import EventType
from argus.events.interfaces import IEventBus
from argus.intent.intent import IntentType


# The Version 1 action_kind value that requires a workflow_id, matching
# argus.dispatcher.action.WorkflowAction.kind's string value ("workflow").
# Deliberately a plain string constant, not an import of WorkflowAction
# itself: argus/capability/ must not depend on argus/dispatcher/ - the
# dependency runs the other way (dispatcher depends on capability), per
# this package's target architecture. If WorkflowAction.kind's value ever
# changes, this constant must be updated to match by hand.
_WORKFLOW_ACTION_KIND = "workflow"


class CapabilityRegistry(ICapabilityRegistry):
    """
    In-memory implementation of ICapabilityRegistry.

    Purpose:
        Be the single source of truth describing everything ArgusOS
        knows how to do, as metadata only. See the module docstring
        for the full design rationale.

    Dependencies:
        An IEventBus implementation, injected by the caller
        (bootstrap.py).
    """

    def __init__(self, event_bus: IEventBus) -> None:
        self._event_bus = event_bus
        self._capabilities: Dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        self._validate_capability(capability)
        if capability.id in self._capabilities:
            raise DuplicateCapabilityError(
                f"A capability with id {capability.id!r} is already registered."
            )
        self._capabilities[capability.id] = capability
        self._publish(
            EventType.CAPABILITY_REGISTERED,
            {"capability_id": capability.id, "name": capability.name},
        )

    def unregister(self, capability_id: str) -> None:
        capability = self._require_capability(capability_id)
        del self._capabilities[capability_id]
        self._publish(
            EventType.CAPABILITY_UNREGISTERED,
            {"capability_id": capability.id, "name": capability.name},
        )

    def get(self, capability_id: str) -> Capability:
        return self._require_capability(capability_id)

    def find_by_intent_type(self, intent_type: IntentType) -> Sequence[Capability]:
        if not isinstance(intent_type, IntentType):
            raise InvalidCapabilityError(
                f"intent_type must be an IntentType, got {intent_type!r}."
            )
        matches: List[Capability] = [
            capability
            for capability in self._capabilities.values()
            if intent_type in capability.intent_types
        ]
        return tuple(matches)

    def list_capabilities(self) -> Sequence[Capability]:
        return tuple(self._capabilities.values())

    def contains(self, capability_id: str) -> bool:
        return isinstance(capability_id, str) and capability_id in self._capabilities

    # -- internals ------------------------------------------------------

    def _require_capability(self, capability_id: str) -> Capability:
        if not isinstance(capability_id, str):
            raise InvalidCapabilityError(
                f"capability_id must be a string, got {capability_id!r}."
            )
        try:
            return self._capabilities[capability_id]
        except KeyError:
            raise CapabilityNotFoundError(
                f"No capability registered with id {capability_id!r}."
            ) from None

    @staticmethod
    def _validate_capability(capability: Capability) -> None:
        if not isinstance(capability, Capability):
            raise InvalidCapabilityError(
                f"register() requires a Capability, got {capability!r}."
            )
        if not capability.id:
            raise InvalidCapabilityError("Capability.id must be non-empty.")
        if not capability.name:
            raise InvalidCapabilityError("Capability.name must be non-empty.")
        if not capability.intent_types:
            raise InvalidCapabilityError(
                "Capability.intent_types must be non-empty."
            )
        for intent_type in capability.intent_types:
            if not isinstance(intent_type, IntentType):
                raise InvalidCapabilityError(
                    f"Every entry in Capability.intent_types must be an "
                    f"IntentType, got {intent_type!r}."
                )
        if not capability.action_kind:
            raise InvalidCapabilityError("Capability.action_kind must be non-empty.")
        if capability.action_kind == _WORKFLOW_ACTION_KIND and not capability.workflow_id:
            raise InvalidCapabilityError(
                f"Capability.workflow_id is required when action_kind is "
                f"{_WORKFLOW_ACTION_KIND!r}."
            )

    def _publish(self, event_type: EventType, payload: dict) -> None:
        self._event_bus.publish(
            Event(type=event_type, source="capability_registry", payload=payload)
        )
