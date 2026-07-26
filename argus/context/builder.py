"""
The ContextBuilder for the ArgusOS Cognitive Context.

Purpose:
    Provide a mutable, fluent way to accumulate a CognitiveContext's
    fields one at a time - across possibly several separate pipeline
    stages - before producing a single immutable CognitiveContext
    snapshot, per factory/packages/022_COGNITIVE_CONTEXT.md. "The
    builder is mutable. The resulting context is immutable." Every
    `with_*` method validates its own input, then mutates this
    builder's internal accumulator state and returns `self`, so calls
    chain: `ContextBuilder().with_conversation(cid).with_memory(mid)
    .build()`.

Accumulate, Except For Conversation:
    with_memory(), with_knowledge(), with_reasoning(), with_decision(),
    and with_metadata() are each called once per item and accumulate -
    calling with_memory() three times with three different reference
    ids produces a CognitiveContext whose memory_references holds all
    three, in call order. with_conversation() is the one exception:
    conversation_id is a single scalar field, not a collection, so
    calling it more than once simply overwrites the previous value -
    the last call before build() wins. This mirrors the same
    "singular field is overwritten, collection field accumulates"
    distinction between CognitiveContext.conversation_id and its four
    Sequence-typed siblings.

with_metadata() Only Ever Populates `extra`:
    ContextMetadata's `created_at`, `version`, and `correlation_id`
    fields are system-assigned at CognitiveContext construction time
    (see metadata.py's own module docstring) - ContextBuilder exposes
    no way to override them. with_metadata(key, value) adds one
    key/value pair to the eventual ContextMetadata.extra mapping;
    calling it multiple times with different keys accumulates, and
    calling it twice with the same key overwrites that key's value -
    the last call wins, the same last-call-wins rule with_conversation
    uses.

Validation Lives Here, Not On CognitiveContext:
    See context.py's own module docstring - CognitiveContext performs
    no validation of its own; every `with_*` method below validates
    its argument before accumulating it, raising InvalidContextError
    for malformed input. build() itself performs no additional
    validation - by the time build() runs, every accumulated value has
    already been validated at the point it was added.

Independent Snapshots:
    build() constructs a fresh CognitiveContext (and a fresh
    ContextMetadata) from this builder's current accumulated state
    every time it is called. Continuing to call `with_*` methods on
    the same builder after calling build() - or calling build() more
    than once - never mutates a CognitiveContext already returned by
    an earlier build() call, since CognitiveContext's own
    __post_init__ copies every mutable sequence/mapping it is given
    (see context.py and metadata.py).

Responsibilities:
    - ContextBuilder: accumulate a CognitiveContext's fields one at a
      time, with per-field validation, and produce an immutable
      CognitiveContext snapshot on build().

Non-Responsibilities:
    - ContextBuilder performs no reasoning, decision-making, or
      service calls - it only validates and accumulates plain data.
    - This module depends on argus.context.context (CognitiveContext),
      argus.context.metadata (ContextMetadata),
      argus.context.exceptions (InvalidContextError),
      argus.context.interfaces (ICognitiveContextBuilder), and
      argus.reasoning.result (ReasoningResult) for with_reasoning()'s
      own type check.

Dependencies:
    argus.context.context (CognitiveContext),
    argus.context.metadata (ContextMetadata),
    argus.context.exceptions (InvalidContextError),
    argus.context.interfaces (ICognitiveContextBuilder),
    argus.reasoning.result (ReasoningResult).
"""

from typing import Any, Dict, List

from argus.context.context import CognitiveContext
from argus.context.exceptions import InvalidContextError
from argus.context.interfaces import ICognitiveContextBuilder
from argus.context.metadata import ContextMetadata
from argus.reasoning.result import ReasoningResult


def _require_non_empty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidContextError(f"{label} must be a non-empty string, got {value!r}.")
    return value


class ContextBuilder(ICognitiveContextBuilder):
    """
    A mutable, fluent builder for CognitiveContext. See the module
    docstring for the full accumulation and validation semantics.
    """

    def __init__(self) -> None:
        self._conversation_id: Any = None
        self._memory_references: List[str] = []
        self._knowledge_references: List[str] = []
        self._reasoning_results: List[ReasoningResult] = []
        self._decision_references: List[str] = []
        self._metadata_extra: Dict[str, Any] = {}

    def with_conversation(self, conversation_id: str) -> "ContextBuilder":
        self._conversation_id = _require_non_empty_string(
            conversation_id, label="conversation_id"
        )
        return self

    def with_memory(self, reference_id: str) -> "ContextBuilder":
        self._memory_references.append(
            _require_non_empty_string(reference_id, label="memory reference_id")
        )
        return self

    def with_knowledge(self, reference_id: str) -> "ContextBuilder":
        self._knowledge_references.append(
            _require_non_empty_string(reference_id, label="knowledge reference_id")
        )
        return self

    def with_reasoning(self, reasoning_result: ReasoningResult) -> "ContextBuilder":
        if not isinstance(reasoning_result, ReasoningResult):
            raise InvalidContextError(
                f"reasoning_result must be a ReasoningResult instance, "
                f"got {reasoning_result!r}."
            )
        self._reasoning_results.append(reasoning_result)
        return self

    def with_decision(self, reference_id: str) -> "ContextBuilder":
        self._decision_references.append(
            _require_non_empty_string(reference_id, label="decision reference_id")
        )
        return self

    def with_metadata(self, key: str, value: Any) -> "ContextBuilder":
        validated_key = _require_non_empty_string(key, label="metadata key")
        self._metadata_extra[validated_key] = value
        return self

    def build(self) -> CognitiveContext:
        return CognitiveContext(
            conversation_id=self._conversation_id,
            memory_references=tuple(self._memory_references),
            knowledge_references=tuple(self._knowledge_references),
            reasoning_results=tuple(self._reasoning_results),
            decision_references=tuple(self._decision_references),
            metadata=ContextMetadata(extra=dict(self._metadata_extra)),
        )
