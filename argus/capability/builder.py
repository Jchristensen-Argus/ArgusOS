"""
The CapabilityBuilder for the ArgusOS Capability Framework.

Purpose:
    Provide a mutable, fluent way to assemble a Capability's fields
    one at a time before producing a single immutable Capability
    snapshot, per factory/packages/033_CAPABILITY_FRAMEWORK.md.
    "Builder is the only mutable object." Directly mirrors
    argus.context.builder.ContextBuilder (022), argus.planning.
    builder.PlanningSessionBuilder (023), argus.trace.builder.
    TraceBuilder (028), argus.task.builder.TaskBuilder (029),
    argus.task_relationship.builder.RelationshipBuilder (031), and
    argus.execution_engine.builder.ExecutionResultBuilder (032) - the
    same fluent-builder pattern applied to Capability, the first time
    Capability (Package 013) has ever had a dedicated builder of its
    own.

Method Surface Beyond The Work Order's Own Six-Item Responsibilities
List:
    This package's own "Responsibilities" list for CapabilityBuilder
    names exactly six items: "assign id, assign name, assign
    description, assign version, assign metadata, build immutable
    Capability" - no mention of intent_types, action_kind,
    workflow_id, or enabled. But Capability's own pre-existing
    (Package 013) constructor requires `name`, `description`,
    `intent_types`, and `action_kind` with no default - a
    CapabilityBuilder that could never set `intent_types`/
    `action_kind` could not actually build a usable Capability at all.
    Resolved the same way this exact gap has been resolved three times
    before (029, 031, 032): the umbrella responsibility is read as
    covering the full field surface the built object actually needs,
    not just the subset the work order happens to name explicitly.
    `with_intent_type()`/`with_intent_types()`/`clear_intent_types()`
    mirror the accumulate/bulk-assign/clear trio already established by
    `TaskBuilder.with_relationship()`-family (031) and
    `ExecutionResultBuilder.with_completed_task()`-family (032).
    `with_action_kind()`/`with_workflow_id()`/`with_enabled()` are
    included for the identical reason - without them, Capabilities
    with a "workflow" action_kind (the only kind Version 1 of this
    codebase's Intent Dispatcher actually resolves) could never be
    built through this builder at all.

with_id() Is Included Despite No Other Builder In This Codebase
Exposing An Equivalent:
    RelationshipBuilder (031) never exposes `with_relationship_id()`;
    ExecutionResultBuilder (032) never exposes
    `with_execution_id()`; TaskBuilder (029) never exposes
    `with_task_id()` - every one of those identity fields is always
    system-assigned, via the value object's own `default_factory`,
    never settable through the builder. This package's own
    Responsibilities list explicitly names "assign id" as one of
    CapabilityBuilder's six items, unlike any of those three
    siblings' own equivalent lists - so, unlike them,
    `with_id()` is implemented, letting a caller override
    Capability's own auto-generated `id` when it chooses to (mirroring
    Capability's own pre-existing constructor, which already accepts
    an explicit `id=` keyword argument - see capability.py). When
    `with_id()` is never called, `build()` lets Capability's own
    `default_factory` generate a fresh id, exactly as if
    CapabilityBuilder had not been used at all.

with_metadata() Populates capability_metadata.extra, Not The
Pre-Existing metadata Field:
    Mirrors `TaskBuilder.with_metadata()` (029), `RelationshipBuilder.
    with_metadata()` (031), and `ExecutionResultBuilder.
    with_metadata()` (032)'s identical shape: `with_metadata(key,
    value)` accumulates into the eventual `CapabilityMetadata.extra`
    mapping (Package 033's own new addition - see metadata.py's and
    capability.py's own module docstrings), not into Capability's
    pre-existing (013) `metadata: Mapping[str, Any]` field, which this
    builder leaves at its own default (`{}`) - the pre-existing field
    is arbitrary caller data with no dedicated builder method of its
    own in Package 013 either, and this package's own Responsibilities
    list does not ask for one.

No Completeness Check, Independent Snapshots:
    Mirrors every other builder in this codebase: `build()` performs
    no validation beyond what each `with_*()` method already validated
    at the point it was called - a Capability built without ever
    calling `with_name()`/`with_description()`/`with_intent_type()`/
    `with_action_kind()` still succeeds, holding empty-string/empty-
    tuple placeholder values, since Capability itself performs no
    field validation of its own (see capability.py's own "Non-
    Responsibilities" note) - the actual, pre-existing (013)
    enforcement of "must be non-empty" lives in
    `CapabilityRegistry.register()`, unchanged by this package. Each
    call to `build()` constructs a fresh, independent Capability (and,
    when `with_id()` was never called, a freshly auto-generated id) -
    continuing to call `with_*()` methods on the same builder after
    `build()`, or calling `build()` more than once, never mutates a
    Capability already returned by an earlier call.

Responsibilities:
    - CapabilityBuilder: assign a Capability's fields one at a time,
      with per-field validation, accumulate its ordered
      `intent_types`, and produce an immutable Capability snapshot on
      build().

Non-Responsibilities:
    - CapabilityBuilder performs no reasoning, dispatch, or execution
      of any kind - it only validates and assigns plain data.
    - CapabilityBuilder is not a service - see interfaces.py's own
      module docstring.
    - CapabilityBuilder does not register the Capability it builds
      into any CapabilityRegistry - that remains an explicit, separate
      caller step, matching every other builder-then-register/
      builder-then-use two-step pattern in this codebase.

Dependencies:
    argus.capability.capability (Capability), argus.capability.metadata
    (CapabilityMetadata), argus.capability.exceptions
    (InvalidCapabilityError), argus.capability.interfaces
    (ICapabilityBuilder), argus.intent.intent (IntentType).
"""

from typing import Any, Dict, List, Optional, Sequence

from argus.capability.capability import Capability
from argus.capability.exceptions import InvalidCapabilityError
from argus.capability.interfaces import ICapabilityBuilder
from argus.capability.metadata import CapabilityMetadata
from argus.intent.intent import IntentType


def _require_non_empty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidCapabilityError(f"{label} must be a non-empty string, got {value!r}.")
    return value


class CapabilityBuilder(ICapabilityBuilder):
    """
    A mutable, fluent builder for Capability. See the module docstring
    for the full assignment and validation semantics.
    """

    def __init__(self) -> None:
        self._id: Optional[str] = None
        self._name: str = ""
        self._description: str = ""
        self._intent_types: List[IntentType] = []
        self._action_kind: str = ""
        self._workflow_id: Optional[str] = None
        self._enabled: bool = True
        self._version: str = "1.0"
        self._metadata_extra: Dict[str, Any] = {}

    def with_id(self, id: str) -> "CapabilityBuilder":
        self._id = _require_non_empty_string(id, label="id")
        return self

    def with_name(self, name: str) -> "CapabilityBuilder":
        self._name = _require_non_empty_string(name, label="name")
        return self

    def with_description(self, description: str) -> "CapabilityBuilder":
        if not isinstance(description, str):
            raise InvalidCapabilityError(
                f"description must be a string, got {description!r}."
            )
        self._description = description
        return self

    def with_intent_type(self, intent_type: IntentType) -> "CapabilityBuilder":
        if not isinstance(intent_type, IntentType):
            raise InvalidCapabilityError(
                f"intent_type must be an IntentType, got {intent_type!r}."
            )
        self._intent_types.append(intent_type)
        return self

    def with_intent_types(self, intent_types: Sequence[IntentType]) -> "CapabilityBuilder":
        if not isinstance(intent_types, (list, tuple)):
            raise InvalidCapabilityError(
                f"intent_types must be a list or tuple of IntentType instances, "
                f"got {intent_types!r}."
            )
        for intent_type in intent_types:
            self.with_intent_type(intent_type)
        return self

    def clear_intent_types(self) -> "CapabilityBuilder":
        self._intent_types = []
        return self

    def with_action_kind(self, action_kind: str) -> "CapabilityBuilder":
        self._action_kind = _require_non_empty_string(action_kind, label="action_kind")
        return self

    def with_workflow_id(self, workflow_id: Optional[str]) -> "CapabilityBuilder":
        if workflow_id is not None and not isinstance(workflow_id, str):
            raise InvalidCapabilityError(
                f"workflow_id must be a string or None, got {workflow_id!r}."
            )
        self._workflow_id = workflow_id
        return self

    def with_enabled(self, enabled: bool) -> "CapabilityBuilder":
        if not isinstance(enabled, bool):
            raise InvalidCapabilityError(f"enabled must be a bool, got {enabled!r}.")
        self._enabled = enabled
        return self

    def with_version(self, version: str) -> "CapabilityBuilder":
        self._version = _require_non_empty_string(version, label="version")
        return self

    def with_metadata(self, key: str, value: Any) -> "CapabilityBuilder":
        validated_key = _require_non_empty_string(key, label="metadata key")
        self._metadata_extra[validated_key] = value
        return self

    def build(self) -> Capability:
        kwargs: Dict[str, Any] = dict(
            name=self._name,
            description=self._description,
            intent_types=tuple(self._intent_types),
            action_kind=self._action_kind,
            workflow_id=self._workflow_id,
            enabled=self._enabled,
            version=self._version,
            capability_metadata=CapabilityMetadata(extra=dict(self._metadata_extra)),
        )
        if self._id is not None:
            kwargs["id"] = self._id
        return Capability(**kwargs)
