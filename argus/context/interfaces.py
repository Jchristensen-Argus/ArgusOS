"""
Public interface contract for the ArgusOS Cognitive Context.

Purpose:
    Define ICognitiveContextBuilder, the contract other modules depend
    on, per factory/packages/022_COGNITIVE_CONTEXT.md.

Architectural Note - This Is Not An IService:
    Every prior infrastructure package in this codebase (013 through
    021) has registered a new core service - even packages like
    Knowledge Graph (018), Reasoning Engine (020), and Decision Engine
    (021), whose own public methods are entirely ungated, still
    inherit IService and are registered with the Lifecycle Manager per
    explicit instruction. Package 022 is different by explicit
    instruction, not by this Engineer's own judgment call: "This is
    not an IService... This package intentionally introduces no new
    core service. This is the first infrastructure package since the
    early foundation that does not expand the service registry."
    ICognitiveContextBuilder therefore extends plain `ABC`, exactly
    matching argus.connectors.interfaces.IConnector's (Package 017)
    own precedent for "a contract that is plain behavior, not a
    lifecycle-managed service" - not IService. Consequently:
    ContextBuilder is never constructed in argus/bootstrap.py, never
    passed to Container.register(), never given a slot in the
    Lifecycle Manager's REGISTERED-state roster, and CognitiveContext/
    ContextBuilder do not appear in CORE_SERVICE_NAMES
    (tests/test_bootstrap.py, argus/tests/test_bootstrap.py) at all.
    Every caller that wants a CognitiveContext simply constructs
    `ContextBuilder()` directly, the same way any caller constructs a
    plain value object like Entity or ReasoningQuery - there is no
    service to look up.

Architectural Note - No Events, No Lifecycle Gating Question:
    Because ContextBuilder is not an IService, the "which methods
    should be gated on RUNNING" question that every IService-adopting
    interface in this codebase documents (see
    argus.decision.interfaces's and argus.reasoning.interfaces's own
    Architectural Notes) simply does not arise here - there is no
    RUNNING state to gate against. Likewise, this package publishes no
    events: "No new EventTypes. This package is intentionally
    passive." Every `with_*` method and build() below either mutates
    this builder's own private, in-process accumulator state or
    constructs a plain value object - neither is the kind of
    externally-visible occurrence this codebase's EventType convention
    exists to announce (compare to DecisionEngine.register_rule() and
    remove_rule(), Package 021's own precedent for "a registry
    mutation need not always publish an event").

Responsibilities:
    - ICognitiveContextBuilder: with_conversation / with_memory /
      with_knowledge / with_reasoning / with_decision / with_metadata
      / build.

Non-Responsibilities:
    - This module implements no behavior; see
      argus.context.builder.ContextBuilder.
    - ICognitiveContextBuilder does not perform reasoning, make
      decisions, execute plans, or call any other service - see this
      package's Objective and Constraints.

Dependencies:
    argus.context.context (CognitiveContext),
    argus.reasoning.result (ReasoningResult).
"""

from abc import ABC, abstractmethod
from typing import Any

from argus.context.context import CognitiveContext
from argus.reasoning.result import ReasoningResult


class ICognitiveContextBuilder(ABC):
    """
    Contract for a mutable, fluent CognitiveContext builder. See this
    module's docstring for why ICognitiveContextBuilder does not
    inherit IService and why this package publishes no events.
    """

    @abstractmethod
    def with_conversation(self, conversation_id: str) -> "ICognitiveContextBuilder":
        """Set this builder's conversation_id. A later call overwrites
        an earlier one - the last call before build() wins. Raises
        InvalidContextError if `conversation_id` is not a non-empty
        string."""

    @abstractmethod
    def with_memory(self, reference_id: str) -> "ICognitiveContextBuilder":
        """Append one memory reference identifier. Accumulates across
        multiple calls. Raises InvalidContextError if `reference_id`
        is not a non-empty string."""

    @abstractmethod
    def with_knowledge(self, reference_id: str) -> "ICognitiveContextBuilder":
        """Append one knowledge reference identifier. Accumulates
        across multiple calls. Raises InvalidContextError if
        `reference_id` is not a non-empty string."""

    @abstractmethod
    def with_reasoning(self, reasoning_result: ReasoningResult) -> "ICognitiveContextBuilder":
        """Append one ReasoningResult. Accumulates across multiple
        calls. Raises InvalidContextError if `reasoning_result` is not
        a ReasoningResult instance."""

    @abstractmethod
    def with_decision(self, reference_id: str) -> "ICognitiveContextBuilder":
        """Append one decision reference identifier. Accumulates
        across multiple calls. Raises InvalidContextError if
        `reference_id` is not a non-empty string."""

    @abstractmethod
    def with_metadata(self, key: str, value: Any) -> "ICognitiveContextBuilder":
        """Set one arbitrary metadata key/value pair on the eventual
        CognitiveContext.metadata.extra mapping. A later call with the
        same key overwrites an earlier one. Raises InvalidContextError
        if `key` is not a non-empty string."""

    @abstractmethod
    def build(self) -> CognitiveContext:
        """Construct and return a new, immutable CognitiveContext
        snapshot from this builder's currently accumulated state.
        Performs no additional validation - every accumulated value
        was already validated by the `with_*` call that added it. Safe
        to call more than once; each call returns an independent
        CognitiveContext."""
