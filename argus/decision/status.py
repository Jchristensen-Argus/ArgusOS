"""
The DecisionRecordStatus enumeration for the ArgusOS Decision
Framework.

Purpose:
    Represent the closed set of states a DecisionRecord may carry, per
    factory/packages/039_DECISION_FRAMEWORK.md. "No transition logic"
    - this module defines only the enumeration itself; nothing in
    this package moves a DecisionRecord from one DecisionRecordStatus
    to another. Mirrors argus.goal.status.GoalStatus's /
    argus.project.status.ProjectStatus's / argus.workspace.status.
    WorkspaceStatus's own shape: a plain `Enum` (not a `str`
    subclass), lowercase string values matching each member's name.

Naming Note - DecisionRecordStatus, Not DecisionStatus:
    This package's own work order names this enum "DecisionStatus."
    argus.decision already contains an unrelated, pre-existing
    concept sharing the word "Decision" - Package 021's Decision
    Engine, whose own `Decision` class is the immutable outcome of
    evaluating ReasoningResult objects against registered
    DecisionRules. This package's own `Decision` - "captures a
    question, the available options, the selected outcome, and the
    reasoning that led to it" - is a structurally and semantically
    unrelated concept that happens to share the same English word.
    Per explicit Founder direction, Package 021's own Decision Engine
    is the canonical owner of the bare `Decision` name within
    argus.decision; this package's own model is named DecisionRecord
    throughout - `DecisionRecord`, `DecisionRecordStatus`,
    `DecisionRecordPriority`, `DecisionRecordMetadata`,
    `DecisionRecordBuilder`, `IDecisionRecordBuilder`,
    `DecisionRecordError`, `InvalidDecisionRecordError` - so that both
    concepts coexist within argus.decision without any symbol,
    filename, or import colliding. See argus/decision/decision_record.
    py's own module docstring for the complete reasoning, and
    factory/packages/039_DECISION_FRAMEWORK.md's own Engineering
    Decision section for the full record.

PENDING Is The Default:
    Continuing this codebase's own "the first-listed member is the
    default" convention, DecisionRecordStatus's own default is
    PENDING - a DecisionRecord awaiting review, the natural starting
    state for a question that has been posed but not yet decided.

No Transitions, No Behavior:
    "Decision is a passive domain object only." No Version 1 code
    anywhere in this package ever constructs a DecisionRecord with any
    status other than whatever a caller explicitly supplies via
    DecisionRecordBuilder.with_status() - the default is
    DecisionRecordStatus.PENDING, and nothing advances it further.

Responsibilities:
    - DecisionRecordStatus: enumerate the five states a
      DecisionRecord's own `status` field may hold.

Non-Responsibilities:
    - This module implements no transition logic, no validation of
      whether a given transition is legal, and no behavior of any
      kind beyond the enumeration itself.

Dependencies:
    None.
"""

from enum import Enum


class DecisionRecordStatus(Enum):
    """
    The closed set of states a DecisionRecord may be in. None of
    these states imply any transition logic - no Version 1 code in
    this codebase moves a DecisionRecord between them.

    PENDING: a DecisionRecord's initial state - the question has been
        posed but no review has begun. Default status for every
        DecisionRecord built via DecisionRecordBuilder that never
        calls with_status().
    IN_REVIEW: a DecisionRecord currently under active consideration.
    APPROVED: a DecisionRecord whose selected outcome has been
        accepted.
    REJECTED: a DecisionRecord whose selected outcome has been
        declined.
    ARCHIVED: a DecisionRecord retained for historical reference,
        no longer under active consideration.
    """

    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"
