"""
The PolicyBuilder for the ArgusOS Policy Framework.

Purpose:
    Provide a mutable, fluent way to assemble a Policy's fields one at
    a time before producing a single immutable Policy snapshot, per
    factory/packages/040_POLICY_FRAMEWORK.md. "Builder is the only
    mutable object." Directly mirrors argus.goal.builder.GoalBuilder
    (038), with `scope` in place of `priority`.

with_scope() Is Explicitly Named, Unlike with_owner()/with_tags():
    This package's own "Responsibilities" list for PolicyBuilder names
    exactly five items plus build: "assign name, assign description,
    assign status, assign scope, assign metadata, build immutable
    Policy." Exactly mirroring GoalBuilder's own identical reasoning
    for `priority` (038): `scope` is a top-level field on Policy
    itself, not a metadata sub-field, and this package's own
    Responsibilities list names "assign scope" as its own explicit
    bullet. `with_scope()` is therefore implemented as a full,
    validated, singular-field setter - the same shape as
    `with_status()`.

with_name() / with_description() / with_status() / with_scope() Are
Singular Fields, Overwritten, Not Accumulated:
    Each of `name`, `description`, `status`, and `scope` is a single
    scalar field on `Policy`, not a collection - calling any of these
    more than once simply overwrites the previous value, the last
    call before build() wins.

with_metadata() Only Ever Populates `extra`:
    PolicyMetadata's `created_at`, `version`, `correlation_id`,
    `owner`, and `tags` fields are all system-managed - not settable
    through PolicyBuilder in Version 1 (see metadata.py's own module
    docstring). `with_metadata(key, value)` adds one key/value pair to
    the eventual `PolicyMetadata.extra` mapping; calling it multiple
    times with different keys accumulates, and calling it twice with
    the same key overwrites that key's value - the last call wins.

No with_policy_id():
    This package's own Responsibilities list does not name "assign
    id" - continuing the "no with_<id>() unless explicitly named"
    precedent already established by ProjectBuilder (036),
    WorkspaceBuilder (037), GoalBuilder (038), and
    DecisionRecordBuilder (039). `policy_id` is left at its own
    fresh-uuid4 default for every Policy this builder produces.

Validation Lives Here, Not On Policy:
    See policy.py's own module docstring - Policy performs no
    validation of its own; every `with_*` method below validates its
    argument before assigning it, raising InvalidPolicyError for
    malformed input.

Independent Snapshots:
    build() constructs a fresh Policy (and a fresh PolicyMetadata)
    from this builder's current accumulated state every time it is
    called.

Responsibilities:
    - PolicyBuilder: assign a Policy's `name`, `description`,
      `status`, `scope`, and `extra` metadata, with per-field
      validation, and produce an immutable Policy snapshot on
      build().

Non-Responsibilities:
    - PolicyBuilder performs no enforcement, evaluation, execution, or
      AI of any kind - it only validates and assigns plain data.
    - PolicyBuilder is not a service - see interfaces.py's own module
      docstring.

Dependencies:
    argus.policy.policy (Policy), argus.policy.status (PolicyStatus),
    argus.policy.scope (PolicyScope), argus.policy.metadata
    (PolicyMetadata), argus.policy.exceptions (InvalidPolicyError),
    argus.policy.interfaces (IPolicyBuilder).
"""

from typing import Any, Dict

from argus.policy.exceptions import InvalidPolicyError
from argus.policy.interfaces import IPolicyBuilder
from argus.policy.metadata import PolicyMetadata
from argus.policy.policy import Policy
from argus.policy.scope import PolicyScope
from argus.policy.status import PolicyStatus


def _require_non_empty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidPolicyError(f"{label} must be a non-empty string, got {value!r}.")
    return value


class PolicyBuilder(IPolicyBuilder):
    """
    A mutable, fluent builder for Policy. See the module docstring for
    the full assignment and validation semantics.
    """

    def __init__(self) -> None:
        self._name: str = ""
        self._description: str = ""
        self._status: PolicyStatus = PolicyStatus.ACTIVE
        self._scope: PolicyScope = PolicyScope.GLOBAL
        self._metadata_extra: Dict[str, Any] = {}

    def with_name(self, name: str) -> "PolicyBuilder":
        self._name = _require_non_empty_string(name, label="name")
        return self

    def with_description(self, description: str) -> "PolicyBuilder":
        if not isinstance(description, str):
            raise InvalidPolicyError(
                f"description must be a string, got {description!r}."
            )
        self._description = description
        return self

    def with_status(self, status: PolicyStatus) -> "PolicyBuilder":
        if not isinstance(status, PolicyStatus):
            raise InvalidPolicyError(
                f"status must be a PolicyStatus instance, got {status!r}."
            )
        self._status = status
        return self

    def with_scope(self, scope: PolicyScope) -> "PolicyBuilder":
        if not isinstance(scope, PolicyScope):
            raise InvalidPolicyError(
                f"scope must be a PolicyScope instance, got {scope!r}."
            )
        self._scope = scope
        return self

    def with_metadata(self, key: str, value: Any) -> "PolicyBuilder":
        validated_key = _require_non_empty_string(key, label="metadata key")
        self._metadata_extra[validated_key] = value
        return self

    def build(self) -> Policy:
        return Policy(
            name=self._name,
            description=self._description,
            status=self._status,
            scope=self._scope,
            metadata=PolicyMetadata(extra=dict(self._metadata_extra)),
        )
