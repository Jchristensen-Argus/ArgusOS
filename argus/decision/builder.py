"""
The DecisionRecordBuilder for the ArgusOS Decision Framework.

Purpose:
    Provide a mutable, fluent way to assemble a DecisionRecord's
    fields one at a time before producing a single immutable
    DecisionRecord snapshot, per
    factory/packages/039_DECISION_FRAMEWORK.md. "Builder is the only
    mutable object." Directly mirrors argus.goal.builder.GoalBuilder
    (038), with `title`/`question` in place of `name`/`description`.

Naming Note - DecisionRecordBuilder, Not DecisionBuilder:
    See decision_record.py's own module docstring for the full
    reasoning: this package's own model is named DecisionRecord
    throughout, to avoid colliding with Package 021's own
    pre-existing, unrelated Decision Engine concept.

with_priority() Is Explicitly Named, Unlike with_owner()/with_tags():
    This package's own "Responsibilities" list for DecisionRecordBuilder
    names exactly five items plus build: "assign title, assign
    question, assign status, assign priority, assign metadata, build
    immutable Decision." Exactly mirroring GoalBuilder's own identical
    reasoning (038): `priority` is a top-level field on DecisionRecord
    itself, not a metadata sub-field, and this package's own
    Responsibilities list names "assign priority" as its own explicit
    bullet. `with_priority()` is therefore implemented as a full,
    validated, singular-field setter - the same shape as
    `with_status()`.

with_title() / with_question() / with_status() / with_priority() Are
Singular Fields, Overwritten, Not Accumulated:
    Each of `title`, `question`, `status`, and `priority` is a single
    scalar field on `DecisionRecord`, not a collection - calling any
    of these more than once simply overwrites the previous value, the
    last call before build() wins.

with_metadata() Only Ever Populates `extra`:
    DecisionRecordMetadata's `created_at`, `version`, `correlation_id`,
    `owner`, and `tags` fields are all system-managed - not settable
    through DecisionRecordBuilder in Version 1 (see metadata.py's own
    module docstring). `with_metadata(key, value)` adds one key/value
    pair to the eventual `DecisionRecordMetadata.extra` mapping;
    calling it multiple times with different keys accumulates, and
    calling it twice with the same key overwrites that key's value -
    the last call wins.

No with_decision_id():
    This package's own Responsibilities list does not name "assign
    id" - continuing the "no with_<id>() unless explicitly named"
    precedent already established by ProjectBuilder (036),
    WorkspaceBuilder (037), and GoalBuilder (038). `decision_id` is
    left at its own fresh-uuid4 default for every DecisionRecord this
    builder produces.

Validation Lives Here, Not On DecisionRecord:
    See decision_record.py's own module docstring - DecisionRecord
    performs no validation of its own; every `with_*` method below
    validates its argument before assigning it, raising
    InvalidDecisionRecordError for malformed input.

Independent Snapshots:
    build() constructs a fresh DecisionRecord (and a fresh
    DecisionRecordMetadata) from this builder's current accumulated
    state every time it is called.

Responsibilities:
    - DecisionRecordBuilder: assign a DecisionRecord's `title`,
      `question`, `status`, `priority`, and `extra` metadata, with
      per-field validation, and produce an immutable DecisionRecord
      snapshot on build().

Non-Responsibilities:
    - DecisionRecordBuilder performs no reasoning, scoring, execution,
      or AI of any kind - it only validates and assigns plain data.
    - DecisionRecordBuilder is not a service - see interfaces.py's own
      module docstring.

Dependencies:
    argus.decision.decision_record (DecisionRecord),
    argus.decision.status (DecisionRecordStatus),
    argus.decision.priority (DecisionRecordPriority),
    argus.decision.metadata (DecisionRecordMetadata),
    argus.decision.exceptions (InvalidDecisionRecordError),
    argus.decision.interfaces (IDecisionRecordBuilder).
"""

from typing import Any, Dict

from argus.decision.decision_record import DecisionRecord
from argus.decision.exceptions import InvalidDecisionRecordError
from argus.decision.interfaces import IDecisionRecordBuilder
from argus.decision.metadata import DecisionRecordMetadata
from argus.decision.priority import DecisionRecordPriority
from argus.decision.status import DecisionRecordStatus


def _require_non_empty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidDecisionRecordError(
            f"{label} must be a non-empty string, got {value!r}."
        )
    return value


class DecisionRecordBuilder(IDecisionRecordBuilder):
    """
    A mutable, fluent builder for DecisionRecord. See the module
    docstring for the full assignment and validation semantics.
    """

    def __init__(self) -> None:
        self._title: str = ""
        self._question: str = ""
        self._status: DecisionRecordStatus = DecisionRecordStatus.PENDING
        self._priority: DecisionRecordPriority = DecisionRecordPriority.NORMAL
        self._metadata_extra: Dict[str, Any] = {}

    def with_title(self, title: str) -> "DecisionRecordBuilder":
        self._title = _require_non_empty_string(title, label="title")
        return self

    def with_question(self, question: str) -> "DecisionRecordBuilder":
        self._question = _require_non_empty_string(question, label="question")
        return self

    def with_status(self, status: DecisionRecordStatus) -> "DecisionRecordBuilder":
        if not isinstance(status, DecisionRecordStatus):
            raise InvalidDecisionRecordError(
                f"status must be a DecisionRecordStatus instance, got {status!r}."
            )
        self._status = status
        return self

    def with_priority(self, priority: DecisionRecordPriority) -> "DecisionRecordBuilder":
        if not isinstance(priority, DecisionRecordPriority):
            raise InvalidDecisionRecordError(
                f"priority must be a DecisionRecordPriority instance, got {priority!r}."
            )
        self._priority = priority
        return self

    def with_metadata(self, key: str, value: Any) -> "DecisionRecordBuilder":
        validated_key = _require_non_empty_string(key, label="metadata key")
        self._metadata_extra[validated_key] = value
        return self

    def build(self) -> DecisionRecord:
        return DecisionRecord(
            title=self._title,
            question=self._question,
            status=self._status,
            priority=self._priority,
            metadata=DecisionRecordMetadata(extra=dict(self._metadata_extra)),
        )
