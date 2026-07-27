"""
The AgentSession value object for the ArgusOS Agent Session package.

Purpose:
    Represent a single, immutable, ongoing interaction between a user
    and Argus: an identity, the one Conversation it owns, and
    arbitrary caller metadata - per
    factory/packages/026_AGENT_SESSION.md. "An Agent Session
    represents an ongoing interaction between a user and Argus. It
    owns conversation continuity." An AgentSession is pure data: it
    does not orchestrate the Cognitive Pipeline itself, does not
    advance its own conversation, and does not know what AgentService
    will eventually do with it.

The Session Owns One Conversation Instance:
    "The session owns one Conversation instance. The Conversation
    remains the authoritative conversation model." `conversation`
    holds the actual, already-immutable `ConversationSession` (Package
    011) itself - produced by `ConversationManager.start_session()`/
    `receive()` elsewhere, never constructed or parsed by this
    package. AgentSession does not duplicate, summarize, or derive any
    conversation state of its own - it holds a direct reference to the
    one authoritative model, the same "hold the actual object, not a
    copy or a re-derivation of it" precedent
    `PlanningSession.cognitive_context` (Package 023) and
    `PipelineRequest.conversation` (Package 025) already established
    one layer below.

`conversation` Is Required; "Empty" Refers To Its Own Message History:
    Mirrors `PipelineRequest.conversation`'s (Package 025) identical
    reasoning, applied one layer up: a session with nothing to own is
    not a meaningful session, so `conversation` has no default of its
    own. "Empty session" (see tests/test_agent_session.py) means an
    AgentSession whose own `conversation.messages` tuple is empty (a
    fresh `ConversationSession()`, itself trivially constructible with
    every one of its own fields defaulted) - not an absent
    `conversation` field. A caller who wants a brand-new, empty
    session therefore still passes `conversation=ConversationSession()`
    explicitly - the same pattern already used throughout
    tests/test_pipeline.py for "empty conversation" cases.

Field Ordering Deviates From The Work Order's Own Listed Order:
    The work order lists AgentSession's fields as `session_id`,
    `conversation`, `metadata` - but `conversation` has no default
    (see above) while `session_id` does (a fresh uuid4). Python
    dataclass field ordering requires every non-default field to
    precede every defaulted field, so `conversation` is declared
    first in the actual code below - the same
    listed-order-vs-declared-order deviation already applied to
    `Entity`, `ReasoningQuery`, `DecisionRule`, `PipelineRequest`, and
    `PipelineResult` whenever an identical tension arose.

No Validation Here - See AgentService (in interfaces.py / a future
service.py):
    Like every other value object in this codebase, AgentSession
    performs no validation of its own fields in __post_init__ beyond
    the standard mutable-to-immutable wrapping (dict ->
    MappingProxyType). AgentService.run() validates its own input
    before orchestrating anything - the same "validation lives in the
    consuming service, not the value object" division of
    responsibility every other package in this codebase already
    follows.

Responsibilities:
    - AgentSession: hold a session identity, the one Conversation it
      owns, and arbitrary caller metadata as an immutable value
      object.

Non-Responsibilities:
    - AgentSession performs no orchestration, reasoning, planning, or
      execution of any kind - see this package's own Objective and
      Constraints.
    - This module depends only on argus.conversation.session
      (ConversationSession) to type its own field - it has no
      dependency on argus.agent.service, matching the "pure,
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
class AgentSession:
    """
    An immutable record of one ongoing interaction between a user and
    Argus. See the module docstring for the full field semantics.

    Fields:
        conversation: The one ConversationSession this session owns.
            Required - see the module docstring's "conversation Is
            Required" note.
        session_id: Unique identifier for this AgentSession. Defaults
            to a fresh uuid4 string.
        metadata: Additional, arbitrary caller-supplied data. Defaults
            to an empty mapping.
    """

    conversation: ConversationSession
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
