"""
The AgentRequest value object for the ArgusOS Agent Session package.

Purpose:
    Represent a single, immutable request to advance one AgentSession
    - the AgentSession it references, the ConversationSession this
    particular request concerns, an identity, and arbitrary caller
    metadata - per factory/packages/026_AGENT_SESSION.md. An
    AgentRequest is pure data: it does not orchestrate the Cognitive
    Pipeline itself, does not advance the session, and does not know
    what AgentService will eventually do with it.

The Request References An AgentSession - And Separately Carries A
Conversation:
    "The request references an AgentSession." `session` holds the
    actual, already-immutable `AgentSession` (this package) this
    request concerns - never constructed or parsed by this module.
    `conversation` is a second, sibling field - not derived from
    `session.conversation` - mirroring `PipelineRequest.conversation`'s
    (Package 025) own role one layer below: the conversation state
    *as of this specific request*, which a caller may supply as the
    session's own already-known conversation, or as a newer
    ConversationSession reflecting a message received since the
    session was last read (for example, produced by
    `ConversationManager.receive()` immediately before constructing
    this request). AgentRequest does not enforce that the two agree -
    see "No Validation Here" below - the same restraint
    `PlanningSession.cognitive_context` (Package 023) and
    `AgentSession.conversation` (this package) already show toward
    objects they hold without independently re-verifying.

Both `session` And `conversation` Are Required:
    Mirrors `PipelineRequest.conversation`'s (Package 025) reasoning,
    applied to two fields instead of one: a request with no session
    to advance, or no conversation to advance it with, is not a
    meaningful request. Neither has a default.

Field Ordering Deviates From The Work Order's Own Listed Order:
    The work order lists AgentRequest's fields as `request_id`,
    `session`, `conversation`, `metadata` - but `session` and
    `conversation` have no default while `request_id` does (a fresh
    uuid4). Python dataclass field ordering requires every non-default
    field to precede every defaulted field, so `session` and
    `conversation` are declared first in the actual code below - the
    same listed-order-vs-declared-order deviation already applied to
    `Entity`, `ReasoningQuery`, `DecisionRule`, `PipelineRequest`,
    `PipelineResult`, and `AgentSession` (this package) whenever an
    identical tension arose.

No Validation Here - See service.py:
    Like every other value object in this codebase, AgentRequest
    performs no validation of its own fields in __post_init__ beyond
    the standard mutable-to-immutable wrapping (dict ->
    MappingProxyType). AgentService.run() validates its own input
    before orchestrating anything - the same "validation lives in the
    consuming service, not the value object" division of
    responsibility every other package in this codebase already
    follows.

Responsibilities:
    - AgentRequest: hold a request identity, the AgentSession it
      references, the ConversationSession it concerns, and arbitrary
      caller metadata as an immutable value object.

Non-Responsibilities:
    - AgentRequest performs no orchestration, reasoning, planning, or
      execution of any kind - see this package's own Objective and
      Constraints.
    - This module depends only on argus.agent.session (AgentSession)
      and argus.conversation.session (ConversationSession) to type its
      own fields - it has no dependency on argus.agent.service,
      matching the "pure, dependency-free leaf" precedent set by
      every other value object in this codebase.

Dependencies:
    argus.agent.session (AgentSession), argus.conversation.session
    (ConversationSession).
"""

import uuid
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from argus.agent.session import AgentSession
from argus.conversation.session import ConversationSession


@dataclass(frozen=True)
class AgentRequest:
    """
    An immutable request to advance one AgentSession. See the module
    docstring for the full field semantics.

    Fields:
        session: The AgentSession this request references. Required -
            see the module docstring's "Both session And conversation
            Are Required" note.
        conversation: The ConversationSession this request concerns.
            Required - see the same note.
        request_id: Unique identifier for this AgentRequest. Defaults
            to a fresh uuid4 string.
        metadata: Additional, arbitrary caller-supplied data, carried
            through to the produced AgentResponse - see service.py's
            own module docstring for exactly how. Defaults to an
            empty mapping.
    """

    session: AgentSession
    conversation: ConversationSession
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
