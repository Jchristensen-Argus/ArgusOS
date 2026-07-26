"""
The CognitiveContext value object for ArgusOS.

Purpose:
    Represent a single, immutable snapshot of the state produced so
    far by one pass through ArgusOS's cognitive pipeline (Conversation
    -> Memory -> Knowledge -> Reasoning -> Cognitive Context ->
    Decision -> Planner -> Runtime) - per
    factory/packages/022_COGNITIVE_CONTEXT.md. "It represents the
    complete state of a reasoning cycle... It is a transport object
    only." A CognitiveContext is pure data: it performs no reasoning,
    makes no decisions, executes no plans, and calls no other
    service - it only carries references and results forward from one
    pipeline stage to the next.

Transport Object, Not A Live Reference:
    CognitiveContext carries `reasoning_results` as actual, already-
    immutable ReasoningResult objects (Package 020) - matching this
    field's own name and directly reusing Decision.reasoning_results'
    (Package 021) identical field name and type. `memory_references`,
    `knowledge_references`, and `decision_references`, by contrast,
    are plain identifier strings (MemoryRecord keys, Knowledge Graph
    Entity/Relationship ids, and Decision.decision_id values,
    respectively) - not the live objects themselves. This asymmetry
    is deliberate, not an oversight: the work order's own field names
    draw the same distinction ("reasoning_results" vs. "...
    references"), and holding bare identifier strings for the other
    three fields is what makes "shall NOT modify any contained
    object" and "shall NOT own persistence" true by construction - a
    CognitiveContext holding only strings has no live object graph to
    accidentally mutate or to be responsible for persisting, and
    introduces no coupling to argus.memory_integration's or
    argus.knowledge_graph's own concrete value-object shapes. This
    mirrors the same "hold an id, not the object" choice
    argus.reasoning.engine.ReasoningEngine made when it deliberately
    declined to reach into MemoryMapper's private `f"memory:{key}"`
    id scheme (see reasoning/engine.py's own Architectural Decision) -
    here applied to CognitiveContext's own field shapes instead.

No Validation Here - See builder.py:
    Like every other value object in this codebase (Entity,
    Relationship, ReasoningQuery, ReasoningResult, DecisionRule,
    Decision), CognitiveContext performs no validation of its own
    fields in __post_init__ beyond the standard mutable-to-immutable
    wrapping (list/tuple -> tuple, dict -> MappingProxyType).
    ContextBuilder (builder.py) is this package's equivalent of a
    "consuming service" for validation purposes - exactly as
    KnowledgeGraph.add_entity() validates an Entity before storing it,
    ContextBuilder's own `with_*` methods validate their input before
    accumulating it, even though ContextBuilder is not an IService and
    CognitiveContext is never "stored" anywhere. CognitiveContext
    remains directly constructible without going through
    ContextBuilder at all (both are tested independently - see
    tests/test_context.py and tests/test_context_builder.py) for the
    same reason every other value object in this codebase is: a pure
    data holder should not force callers through one particular
    construction path.

Responsibilities:
    - CognitiveContext: hold a conversation identifier, memory/
      knowledge/decision reference identifiers, reasoning results, and
      descriptive metadata as a single immutable value object.

Non-Responsibilities:
    - CognitiveContext performs no reasoning, decision-making, plan
      execution, or service calls of any kind - see this package's own
      Objective and Constraints.
    - CognitiveContext is not consumed by the Planner or the Decision
      Engine in Version 1 - "Package 022 introduces the abstraction
      only." See factory/packages/022_COGNITIVE_CONTEXT.md's own
      Version 1 Limitations.
    - This module depends only on argus.reasoning.result
      (ReasoningResult) and argus.context.metadata (ContextMetadata)
      to type its own fields - it has no dependency on
      argus.context.builder, matching the "pure, dependency-free leaf"
      precedent set by every other value object in this codebase.

Dependencies:
    argus.reasoning.result (ReasoningResult),
    argus.context.metadata (ContextMetadata).
"""

import uuid
from dataclasses import dataclass, field
from typing import Optional, Sequence

from argus.context.metadata import ContextMetadata
from argus.reasoning.result import ReasoningResult


@dataclass(frozen=True)
class CognitiveContext:
    """
    An immutable transport object carrying one reasoning cycle's
    accumulated state through ArgusOS's cognitive pipeline. See the
    module docstring for the full field semantics.

    Fields:
        context_id: Unique identifier for this CognitiveContext.
            Defaults to a fresh uuid4 string.
        conversation_id: The conversation this context belongs to.
            Defaults to None (a context need not be tied to any
            conversation - see the "empty context" test scenarios in
            tests/test_context.py).
        memory_references: Identifier strings for the Memory
            Integration records relevant to this reasoning cycle.
            Defaults to an empty tuple.
        knowledge_references: Identifier strings for the Knowledge
            Graph entities/relationships relevant to this reasoning
            cycle. Defaults to an empty tuple.
        reasoning_results: The actual ReasoningResult objects produced
            during this reasoning cycle. Defaults to an empty tuple.
        decision_references: Identifier strings for the Decisions
            relevant to this reasoning cycle. Defaults to an empty
            tuple.
        metadata: Descriptive bookkeeping about this CognitiveContext
            itself (creation timestamp, schema version, correlation
            id, and arbitrary extra data). Defaults to a fresh
            ContextMetadata.
    """

    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: Optional[str] = None
    memory_references: Sequence[str] = field(default_factory=tuple)
    knowledge_references: Sequence[str] = field(default_factory=tuple)
    reasoning_results: Sequence[ReasoningResult] = field(default_factory=tuple)
    decision_references: Sequence[str] = field(default_factory=tuple)
    metadata: ContextMetadata = field(default_factory=ContextMetadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "memory_references", tuple(self.memory_references))
        object.__setattr__(self, "knowledge_references", tuple(self.knowledge_references))
        object.__setattr__(self, "reasoning_results", tuple(self.reasoning_results))
        object.__setattr__(self, "decision_references", tuple(self.decision_references))
