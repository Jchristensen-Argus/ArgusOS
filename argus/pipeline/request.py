"""
The PipelineRequest value object for the ArgusOS Cognitive Pipeline.

Purpose:
    Represent a single, immutable request to run one pass through the
    cognitive pipeline - the existing ConversationSession it concerns,
    an identity, and arbitrary caller metadata - per
    factory/packages/025_COGNITIVE_PIPELINE.md. A PipelineRequest is
    pure data: it does not run the pipeline itself, does not classify
    or process any raw text, and does not know what CognitivePipeline
    will eventually do with it.

The Request Carries An Existing ConversationSession - Never Raw Text:
    "The request contains the existing Conversation object. Do not
    introduce raw text processing here." `conversation` holds the
    actual, already-immutable `ConversationSession` (Package 011)
    itself - produced by `ConversationManager.start_session()`/
    `receive()` elsewhere, never constructed or parsed by this
    package. This package implements no text classification, no
    intent parsing, and no message handling of any kind - all of that
    already exists (Intent Router, Conversation Manager) and is
    entirely out of scope here, per this package's own explicit
    Objective ("It does not introduce new reasoning").

`conversation` Is Required; "Empty" Refers To Its Own Message History:
    Unlike `CognitiveContext.conversation_id` (Package 022, an
    optional string), `PipelineRequest.conversation` has no default -
    a request with nothing to orchestrate around is not a meaningful
    request. "Empty conversation" (see tests/test_pipeline.py) means a
    `ConversationSession` whose own `messages` tuple is empty (the
    `ConversationSession` default, produced by a fresh
    `start_session()` call before any `receive()` call) - not an
    absent `conversation` field.

No Validation Here - See pipeline.py:
    Like every other value object in this codebase, PipelineRequest
    performs no validation of its own fields in __post_init__ beyond
    the standard mutable-to-immutable wrapping (dict ->
    MappingProxyType). `CognitivePipeline.run()` validates its own
    input before orchestrating anything - the same "validation lives
    in the consuming service, not the value object" division of
    responsibility every other package in this codebase already
    follows.

Responsibilities:
    - PipelineRequest: hold a request identity, an existing
      ConversationSession, and arbitrary caller metadata as an
      immutable value object.

Non-Responsibilities:
    - PipelineRequest performs no orchestration, reasoning, planning,
      or execution of any kind - see this package's own Objective and
      Constraints.
    - This module depends only on argus.conversation.session
      (ConversationSession) to type its own field - it has no
      dependency on argus.pipeline.pipeline, matching the "pure,
      dependency-free leaf" precedent set by every other value object
      in this codebase.

Dependencies:
    argus.conversation.session (ConversationSession).
"""

import uuid
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from argus.conversation.session import ConversationSession


@dataclass(frozen=True)
class PipelineRequest:
    """
    An immutable request to run one pass through the Cognitive
    Pipeline. See the module docstring for the full field semantics.

    Fields:
        conversation: The existing ConversationSession this request
            concerns. Required - see the module docstring's "conversation
            Is Required" note.
        request_id: Unique identifier for this PipelineRequest.
            Defaults to a fresh uuid4 string.
        metadata: Additional, arbitrary caller-supplied data, carried
            through to the produced CognitiveContext, PlanningSession,
            and PipelineResult - see pipeline.py's own module
            docstring for exactly how. Defaults to an empty mapping.
    """

    conversation: ConversationSession
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
