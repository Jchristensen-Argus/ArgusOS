"""
The AutomationBuilder for the ArgusOS Automation Framework.

Purpose:
    Provide a mutable, fluent way to assemble an Automation's fields
    one at a time before producing a single immutable Automation
    snapshot, per factory/packages/041_AUTOMATION_FRAMEWORK.md.
    "Builder is the only mutable object." Directly mirrors
    argus.policy.builder.PolicyBuilder (040), with `trigger` in place
    of `scope`.

with_trigger() Is Explicitly Named, Unlike with_owner()/with_tags():
    This package's own "Responsibilities" list for AutomationBuilder
    names exactly five items plus build: "assign name, assign
    description, assign status, assign trigger, assign metadata,
    build immutable Automation." Exactly mirroring PolicyBuilder's own
    identical reasoning for `scope` (040): `trigger` is a top-level
    field on Automation itself, not a metadata sub-field, and this
    package's own Responsibilities list names "assign trigger" as its
    own explicit bullet. `with_trigger()` is therefore implemented as
    a full, validated, singular-field setter - the same shape as
    `with_status()`.

with_name() / with_description() / with_status() / with_trigger() Are
Singular Fields, Overwritten, Not Accumulated:
    Each of `name`, `description`, `status`, and `trigger` is a single
    scalar field on `Automation`, not a collection - calling any of
    these more than once simply overwrites the previous value, the
    last call before build() wins.

with_metadata() Only Ever Populates `extra`:
    AutomationMetadata's `created_at`, `version`, `correlation_id`,
    `owner`, and `tags` fields are all system-managed - not settable
    through AutomationBuilder in Version 1 (see metadata.py's own
    module docstring). `with_metadata(key, value)` adds one key/value
    pair to the eventual `AutomationMetadata.extra` mapping; calling
    it multiple times with different keys accumulates, and calling it
    twice with the same key overwrites that key's value - the last
    call wins.

No with_automation_id():
    This package's own Responsibilities list does not name "assign
    id" - continuing the "no with_<id>() unless explicitly named"
    precedent already established by ProjectBuilder (036),
    WorkspaceBuilder (037), GoalBuilder (038),
    DecisionRecordBuilder (039), and PolicyBuilder (040).
    `automation_id` is left at its own fresh-uuid4 default for every
    Automation this builder produces.

Validation Lives Here, Not On Automation:
    See automation.py's own module docstring - Automation performs no
    validation of its own; every `with_*` method below validates its
    argument before assigning it, raising InvalidAutomationError for
    malformed input.

Independent Snapshots:
    build() constructs a fresh Automation (and a fresh
    AutomationMetadata) from this builder's current accumulated state
    every time it is called.

Responsibilities:
    - AutomationBuilder: assign an Automation's `name`, `description`,
      `status`, `trigger`, and `extra` metadata, with per-field
      validation, and produce an immutable Automation snapshot on
      build().

Non-Responsibilities:
    - AutomationBuilder performs no scheduling, event handling,
      condition evaluation, or execution of any kind - it only
      validates and assigns plain data.
    - AutomationBuilder is not a service - see interfaces.py's own
      module docstring.

Dependencies:
    argus.automation.automation (Automation), argus.automation.status
    (AutomationStatus), argus.automation.trigger (AutomationTrigger),
    argus.automation.metadata (AutomationMetadata),
    argus.automation.exceptions (InvalidAutomationError),
    argus.automation.interfaces (IAutomationBuilder).
"""

from typing import Any, Dict

from argus.automation.automation import Automation
from argus.automation.exceptions import InvalidAutomationError
from argus.automation.interfaces import IAutomationBuilder
from argus.automation.metadata import AutomationMetadata
from argus.automation.status import AutomationStatus
from argus.automation.trigger import AutomationTrigger


def _require_non_empty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidAutomationError(
            f"{label} must be a non-empty string, got {value!r}."
        )
    return value


class AutomationBuilder(IAutomationBuilder):
    """
    A mutable, fluent builder for Automation. See the module docstring
    for the full assignment and validation semantics.
    """

    def __init__(self) -> None:
        self._name: str = ""
        self._description: str = ""
        self._status: AutomationStatus = AutomationStatus.ACTIVE
        self._trigger: AutomationTrigger = AutomationTrigger.MANUAL
        self._metadata_extra: Dict[str, Any] = {}

    def with_name(self, name: str) -> "AutomationBuilder":
        self._name = _require_non_empty_string(name, label="name")
        return self

    def with_description(self, description: str) -> "AutomationBuilder":
        if not isinstance(description, str):
            raise InvalidAutomationError(
                f"description must be a string, got {description!r}."
            )
        self._description = description
        return self

    def with_status(self, status: AutomationStatus) -> "AutomationBuilder":
        if not isinstance(status, AutomationStatus):
            raise InvalidAutomationError(
                f"status must be an AutomationStatus instance, got {status!r}."
            )
        self._status = status
        return self

    def with_trigger(self, trigger: AutomationTrigger) -> "AutomationBuilder":
        if not isinstance(trigger, AutomationTrigger):
            raise InvalidAutomationError(
                f"trigger must be an AutomationTrigger instance, got {trigger!r}."
            )
        self._trigger = trigger
        return self

    def with_metadata(self, key: str, value: Any) -> "AutomationBuilder":
        validated_key = _require_non_empty_string(key, label="metadata key")
        self._metadata_extra[validated_key] = value
        return self

    def build(self) -> Automation:
        return Automation(
            name=self._name,
            description=self._description,
            status=self._status,
            trigger=self._trigger,
            metadata=AutomationMetadata(extra=dict(self._metadata_extra)),
        )
