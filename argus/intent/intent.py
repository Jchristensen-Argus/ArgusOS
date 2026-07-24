"""
Intent and IntentType for the ArgusOS Intent Router.

Purpose:
    Represent a single, immutable, deterministically-classified
    natural-language request, per factory/packages/009_INTENT_ROUTER.md.

Responsibilities:
    - IntentType: the closed set of intent classifications the parser
      may produce (QUESTION, COMMAND, MEMORY, SCHEDULE, UNKNOWN).
    - Intent: hold identity (id), classification (name), the parser's
      confidence in that classification, any recognized entities and
      auxiliary parameters, and when it was produced (timestamp).

Non-Responsibilities:
    - Intent does not parse text or decide its own classification;
      that is argus.intent.parser's responsibility.
    - Intent does not route itself or invoke anything; that is
      IntentRouter's responsibility.
    - Intent does not validate its own fields (for example, that
      confidence is within 0.0-1.0); that is the parser's
      responsibility, matching the validation precedent set by
      ScheduledTask/KnowledgeRecord/MemoryRecord (data objects across
      this codebase contain no business logic).
    - Like every other value object in this codebase, Intent does not
      deep-freeze `entities`/`parameters`' own contents beyond wrapping
      the top-level mapping in MappingProxyType.

Dependencies:
    None (standard library only).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class IntentType(Enum):
    """The closed set of intent classifications IntentRouter's parser
    may produce. Unrecognized input always classifies as UNKNOWN -
    parsing a valid string never fails, per
    factory/packages/009_INTENT_ROUTER.md."""

    QUESTION = "question"
    COMMAND = "command"
    MEMORY = "memory"
    SCHEDULE = "schedule"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Intent:
    """
    An immutable record of one parsed natural-language request.

    Purpose:
        Carry a request's classification, confidence, and any
        recognized structure through the Intent Router without
        exposing any way to mutate it after construction.

    Responsibilities:
        - Store name, confidence, id, entities, parameters, and
          timestamp.
        - Auto-generate `id` and `timestamp` when not supplied, and
          default `entities`/`parameters` to immutable empty mappings.

    Dependencies:
        None.
    """

    name: IntentType
    confidence: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entities: Mapping[str, Any] = field(default_factory=dict)
    parameters: Mapping[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        # Frozen dataclasses require object.__setattr__ during
        # __post_init__. Matches the immutability guarantee
        # established for Event (Package 003), ServiceDescriptor
        # (Package 004), KnowledgeRecord (Package 006), and
        # MemoryRecord (Package 007).
        object.__setattr__(self, "entities", MappingProxyType(dict(self.entities)))
        object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))
