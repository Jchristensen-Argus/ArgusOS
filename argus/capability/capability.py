"""
The Capability value object for the ArgusOS Capability Registry.

Purpose:
    Represent a single, immutable description of "one thing ArgusOS
    knows how to do" - metadata only, per
    factory/packages/013_CAPABILITY_REGISTRY.md, as amended by
    factory/packages/033_CAPABILITY_FRAMEWORK.md. A Capability is pure
    data: it does not execute anything, does not hold a live service
    reference, and does not know how to translate itself into an
    Action - that translation is CapabilityRegistry's caller's
    responsibility (see argus/dispatcher/action.py's
    build_action_from_capability), matching the precedent set by
    every other value object in this codebase (Workflow, Intent,
    ConversationSession) holding no live service reference of its
    own.

Package 033 Amendment - Capability Gains version And
capability_metadata:
    "Introduce the Capability Framework. A Capability represents a
    pluggable unit of functionality that can eventually execute
    specific types of Tasks." Package 033's own Requirements list a
    five-field shape for Capability: `capability_id, name,
    description, version, metadata`. Per the Founder's explicit
    instruction ("Package 013 already introduced argus/capability/.
    Do not create a parallel package or replace the existing
    implementation... evolve those classes rather than duplicating
    them... preserving backward compatibility wherever practical"),
    this package extends the existing Capability in place rather than
    replacing it:

    - `capability_id`: Capability (013) already has an identity
      field, `id` (auto-generated uuid4, the same field
      `CapabilityRegistry`/`IntentDispatcher`/every existing test and
      bootstrap.py already key and read by). Renaming it to
      `capability_id` would break every one of those call sites -
      "preserving backward compatibility wherever practical" - so no
      rename occurs. Package 033's own "capability_id" is understood
      to refer to this pre-existing `id` field; this is a documented
      naming-convention reconciliation, not a design gap, the same
      "work order names differ from the established convention;
      normalize to the convention and document it" resolution applied
      repeatedly in this codebase (most recently the metadata
      field-order normalization in Packages 028/029/031/032).
    - `name`, `description`: already present, unchanged.
    - `version`: genuinely new - Capability (013) had no version
      field of its own. Added as `version: str`, defaulting to
      `"1.0"`, declared after the pre-existing `enabled` field and
      before `metadata`.
    - `metadata`: Capability (013) already has a `metadata: Mapping[
      str, Any]` field - arbitrary, free-form caller data, with no
      dedicated value-object type. Package 033 also asks for a
      dedicated `CapabilityMetadata` (created_at/version/
      correlation_id/extra), matching the "value object with a
      dedicated *Metadata sibling" convention set since Package 022.
      Retyping the pre-existing `metadata` field to
      `CapabilityMetadata` would break every existing caller/test
      constructing `Capability(metadata={...})` and reading
      `capability.metadata` as a plain mapping (see
      tests/test_capability.py's own `MappingProxyType`/subscript
      assertions) - a real backward-compatibility break, not merely a
      cosmetic one. Instead, Capability gains a *second*, new field,
      `capability_metadata: CapabilityMetadata`, declared last -
      satisfying this package's own "metadata last" requirement from
      the perspective of the dedicated-metadata-object family this
      new field belongs to, while the pre-existing `metadata` field's
      own type, position (immediately before the new field), and
      behavior are completely untouched. See metadata.py's own module
      docstring and factory/packages/033_CAPABILITY_FRAMEWORK.md's own
      Engineering Decision section for the complete reasoning.

    No pre-existing field (`name`, `description`, `intent_types`,
    `action_kind`, `id`, `workflow_id`, `enabled`, `metadata`) was
    renamed, retyped, removed, or repositioned relative to the others.
    Every `Capability(...)` call site that worked before Package 033
    still works unchanged, since both new fields default.

Responsibilities:
    - Hold identity (id), descriptive metadata (name, description),
      the set of IntentTypes this capability handles (intent_types),
      which kind of Action realizes it (action_kind, matching
      argus.dispatcher.action.Action.kind values), the Version-1-
      specific workflow_id when action_kind is "workflow", whether
      the capability is currently enabled, arbitrary caller metadata,
      a version string (Package 033), and dedicated bookkeeping
      metadata (Package 033).
    - Auto-generate `id` when not supplied. Guarantee immutability
      (frozen dataclass) and prevent mutation of the `intent_types`
      sequence or `metadata` mapping after construction.

Non-Responsibilities:
    - Capability does not validate its own fields (for example, that
      intent_types is non-empty, or that workflow_id is present when
      action_kind is "workflow") - that is CapabilityRegistry.
      register()'s responsibility (and, as of Package 033,
      CapabilityBuilder's own with_*() methods), matching the
      validation precedent set by Intent/Workflow/ConversationSession/
      ConversationMessage: data objects across this codebase contain
      no business logic.
    - Capability does not construct, obtain, or reference any Action
      or IWorkflowEngine - it is pure, serializable-shaped data.
    - Capability performs no execution of any kind, per Package 033's
      own explicit Objective: "For Package 033: No real work is
      performed. No tools are invoked. No AI is called. No external
      APIs are used."

Dependencies:
    argus.intent.intent (IntentType), for typing intent_types.
    argus.capability.metadata (CapabilityMetadata) - Package 033.
"""

import uuid
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Optional, Sequence

from argus.capability.metadata import CapabilityMetadata
from argus.intent.intent import IntentType


@dataclass(frozen=True)
class Capability:
    """
    An immutable record describing one thing ArgusOS knows how to do.

    Purpose:
        Let the Capability Registry, the Intent Dispatcher, and any
        future caller (including, as of Package 033, the Execution
        Engine's own future dispatch model) describe and discover
        available capabilities without any of them executing anything
        - see the module docstring.

    Responsibilities:
        - Store name, description, intent_types, action_kind, id,
          workflow_id, enabled, metadata, version, and
          capability_metadata.
        - Auto-generate `id` when not supplied, default `enabled` to
          True, `metadata` to an empty mapping, `version` to `"1.0"`,
          and `capability_metadata` to a fresh CapabilityMetadata, and
          make `intent_types` and `metadata` immutable containers.

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
    version: str = "1.0"
    metadata: Mapping[str, Any] = field(default_factory=dict)
    capability_metadata: CapabilityMetadata = field(default_factory=CapabilityMetadata)

    def __post_init__(self) -> None:
        # Frozen dataclasses require object.__setattr__ during
        # __post_init__. Wrapping `intent_types` in a tuple and
        # `metadata` in MappingProxyType makes the containers
        # themselves read-only, not just the attribute reference -
        # the same pattern used by Workflow.steps/metadata (Package
        # 010) and Intent.entities/parameters (Package 009).
        object.__setattr__(self, "intent_types", tuple(self.intent_types))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
