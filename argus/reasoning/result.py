"""
The ReasoningResult value object for the ArgusOS Reasoning Engine.

Purpose:
    Represent a single, immutable, descriptive-only outcome of a
    Reasoning Engine query - the Entities and Relationships matched,
    a factual trace of the deterministic steps taken to find them, and
    any additional descriptive metadata - per
    factory/packages/020_REASONING_ENGINE.md. "The result is
    descriptive only. No confidence scores. No AI-generated
    explanations." A ReasoningResult is pure data: it is returned by
    every public method of argus.reasoning.engine.ReasoningEngine and
    performs no computation of its own.

Descriptive-Only Discipline:
    `reasoning_steps` is a plain tuple of short, mechanical strings
    describing what the engine actually did (for example, "resolved
    root entity 'e1'", "hop 1: discovered 2 new entities via 3
    relationships") - a factual execution trace, not a narrative
    explanation, and never produced by an LLM or any probabilistic
    process (this package's own Constraints forbid both outright).
    `metadata` similarly holds only plain, mechanically-derived data
    (counts, the query branch taken, structured path listings for
    find_paths(), and the injected IMemoryIntegration's own
    synchronization_status() snapshot - see engine.py's own
    Architectural Decision on that last one) - never a confidence
    score, ranking, or generated-text explanation.

Responsibilities:
    - ReasoningResult: hold a query's matched Entities, matched
      Relationships, execution trace, and descriptive metadata as an
      immutable value object.

Non-Responsibilities:
    - ReasoningResult performs no computation, filtering, or
      traversal itself - see argus.reasoning.engine.ReasoningEngine
      for all query logic.
    - This module depends only on argus.knowledge_graph's own value
      objects (Entity, Relationship) to type its two Sequence fields -
      it has no dependency on argus.reasoning.query or
      argus.reasoning.engine, matching the "pure, dependency-free
      leaf" precedent set by every other value object in this
      codebase.

Dependencies:
    argus.knowledge_graph.entity (Entity),
    argus.knowledge_graph.relationship (Relationship).
"""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from argus.knowledge_graph.entity import Entity
from argus.knowledge_graph.relationship import Relationship


@dataclass(frozen=True)
class ReasoningResult:
    """
    An immutable, descriptive-only outcome of a single Reasoning
    Engine query. See the module docstring for the full field
    semantics.

    Fields:
        matched_entities: Every Entity the query matched. Defaults to
            an empty tuple.
        matched_relationships: Every Relationship the query matched.
            Defaults to an empty tuple.
        reasoning_steps: A factual, mechanical trace of the
            deterministic steps taken to produce this result. Defaults
            to an empty tuple.
        metadata: Additional descriptive data about the result (for
            example, counts, the query branch taken, or structured
            path listings). Defaults to an empty mapping. Never a
            confidence score or generated-text explanation.
    """

    matched_entities: Sequence[Entity] = field(default_factory=tuple)
    matched_relationships: Sequence[Relationship] = field(default_factory=tuple)
    reasoning_steps: Sequence[str] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "matched_entities", tuple(self.matched_entities))
        object.__setattr__(self, "matched_relationships", tuple(self.matched_relationships))
        object.__setattr__(self, "reasoning_steps", tuple(self.reasoning_steps))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
