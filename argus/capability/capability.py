"""
The Capability value object for the ArgusOS Capability Registry.

Purpose:
    Represent a single, immutable description of "one thing ArgusOS
    knows how to do" - metadata only, per
    factory/packages/013_CAPABILITY_REGISTRY.md. A Capability is pure
    data: it does not execute anything, does not hold a live service
    reference, and does not know how to translate itself into an
    Action - that translation is CapabilityRegistry's caller's
    responsibility (see argus/dispatcher/action.py's
    build_action_from_capability), matching the precedent set by
    every other value object in this codebase (Workflow, Intent,
    ConversationSession) holding no live service reference of its
    own.

Responsibilities:
    - Hold identity (id), descriptive metadata (name, description),
      the set of IntentTypes this capability handles (intent_types),
      which kind of Action realizes it (action_kind, matching
      argus.dispatcher.action.Action.kind values), the Version-1-
      specific workflow_id when action_kind is "workflow", whether
      the capability is currently enabled, and arbitrary caller
      metadata.
    - Auto-generate `id` when not supplied. Guarantee immutability
      (frozen dataclass) and prevent mutation of the `intent_types`
      sequence or `metadata` mapping after construction.

Non-Responsibilities:
    - Capability does not validate its own fields (for example, that
      intent_types is non-empty, or that workflow_id is present when
      action_kind is "workflow") - that is CapabilityRegistry.
      register()'s responsibility, matching the validation precedent
      set by Intent/Workflow/ConversationSession/ConversationMessage:
      data objects across this codebase contain no business logic.
    - Capability does not construct, obtain, or reference any Action
      or IWorkflowEngine - it is pure, serializable-shaped data.

Dependencies:
    argus.intent.intent (IntentType), for typing intent_types.
"""

import uuid
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Optional, Sequence

from argus.intent.intent import IntentType


@dataclass(frozen=True)
class Capability:
    """
    An immutable record describing one thing ArgusOS knows how to do.

    Purpose:
        Let the Capability Registry, the Intent Dispatcher, and any
        future caller describe and discover available capabilities
        without any of them executing anything - see the module
        docstring.

    Responsibilities:
        - Store name, description, intent_types, action_kind, id,
          workflow_id, enabled, and metadata.
        - Auto-generate `id` when not supplied, default `enabled` to
          True and `metadata` to an empty mapping, and make
          `intent_types` and `metadata` immutable containers.

    Dependencies:
        None.
    """

    name: str
    description: str
    intent_types: Sequence[IntentType]
    action_kind: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: Optional[str] = None
    enabled: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Frozen dataclasses require object.__setattr__ during
        # __post_init__. Wrapping `intent_types` in a tuple and
        # `metadata` in MappingProxyType makes the containers
        # themselves read-only, not just the attribute reference -
        # the same pattern used by Workflow.steps/metadata (Package
        # 010) and Intent.entities/parameters (Package 009).
        object.__setattr__(self, "intent_types", tuple(self.intent_types))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
