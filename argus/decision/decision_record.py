"""
The DecisionRecord value object for the ArgusOS Decision Framework.

Purpose:
    Represent a single, immutable captured decision within a Project -
    "a Decision captures a question, the available options, the
    selected outcome, and the reasoning that led to it" - per
    factory/packages/039_DECISION_FRAMEWORK.md. This package
    introduces the DecisionRecord model only - no ownership
    relationship to Project (above) or Goal/Plan/Task (siblings/below)
    is implemented yet; see "Future Relationship" below.

Naming Note - DecisionRecord, Not Decision, And decision_record.py,
Not decision.py:
    This package's own work order names this class "Decision" and
    this module "decision.py." Both names are already taken within
    argus.decision by Package 021's own Decision Engine: `Decision`
    (argus/decision/decision.py) is the immutable outcome of
    evaluating one or more ReasoningResult objects against registered
    DecisionRules - "matched_rules, reasoning_results, metadata" - a
    structurally and semantically unrelated concept from this
    package's own "captures a question, the available options, the
    selected outcome, and the reasoning that led to it," sharing only
    the English word "decision." Overwriting argus/decision/decision.py
    or redefining `Decision` would silently break the live
    DecisionEngine core service (constructed and wired in
    bootstrap.py, per Package 021) and every one of its own existing
    tests and callers - a regression this package's own "no
    Bootstrap changes... no regressions" requirements explicitly
    forbid, and directly contrary to the Founder's own explicit
    instruction: "Package 021 already defines the canonical Decision
    package. Do not replace it or introduce a conflicting `Decision`
    type. Instead, extend the existing package by introducing a
    separate historical decision model (using non-conflicting names
    that fit the package conventions) while preserving complete
    backward compatibility with the Decision Engine and all existing
    interfaces." This module is therefore named decision_record.py,
    and its class DecisionRecord, with every sibling symbol renamed
    to match (DecisionRecordStatus, DecisionRecordPriority,
    DecisionRecordMetadata, DecisionRecordBuilder,
    IDecisionRecordBuilder, DecisionRecordError,
    InvalidDecisionRecordError). metadata.py, builder.py, status.py,
    and priority.py did not already exist in argus.decision and are
    therefore created with exactly the filenames this package's own
    work order specifies - only decision.py itself, and the bare
    `Decision` name, are renamed, the minimum deviation needed to
    eliminate the collision. See
    factory/packages/039_DECISION_FRAMEWORK.md's own Engineering
    Decision section for the complete record, and
    argus/decision/engine.py / argus/decision/decision.py / argus/
    decision/rule.py, all three of which remain byte-for-byte
    unmodified by this package.

Every Field Defaults - DecisionRecord() Is Always Valid:
    DecisionRecord has its own dedicated DecisionRecordBuilder - the
    same "value object with a dedicated builder" shape Goal (038),
    Project (036), and Workspace (037) all use, each of which lets
    every field default and leaves construction-time validation to
    the builder's own with_*() methods (see builder.py's own module
    docstring). `decision_id` defaults to a fresh uuid4 string,
    `title` and `question` both default to `""`, `status` defaults to
    `DecisionRecordStatus.PENDING`, `priority` defaults to
    `DecisionRecordPriority.NORMAL`, `metadata` defaults to a fresh
    `DecisionRecordMetadata()`. `DecisionRecord()` with no arguments
    is therefore always valid.

title/question, Not name/description:
    Unlike Project/Workspace/Goal (each holding `name`/`description`),
    this package's own explicit field list reads "decision_id, title,
    question, status, priority, metadata" - `title` and `question`,
    not `name` and `description`. This is a literal reading of this
    package's own distinct field list, not an inconsistency to smooth
    over: a DecisionRecord's own defining content is the question
    being decided, not a general-purpose description.

No Validation Here - See builder.py:
    Like every other value object in this codebase, DecisionRecord
    performs no validation of its own fields - it has no
    `__post_init__` at all, mirroring Goal's/Project's/Workspace's own
    identical shape.

Future Relationship - A DecisionRecord Will Eventually Own Or
Reference Options, Evidence, Supporting Documents, Confidence,
Rationale, Outcome, Review History:
    Per this package's own explicit "Future Relationship" section.
    "Do NOT implement these relationships. Document them only."
    DecisionRecord therefore holds no field referencing any of these
    in Version 1.

Responsibilities:
    - DecisionRecord: hold identity (`decision_id`), a human-readable
      `title` and `question`, its own `status` and `priority`, and
      descriptive `DecisionRecordMetadata`, as an immutable value
      object.

Non-Responsibilities:
    - DecisionRecord performs no reasoning, scoring, execution, or AI
      of any kind - "Decision is a passive domain object only."
    - DecisionRecord owns no Options, Evidence, Supporting documents,
      Confidence, Rationale, Outcome, or Review history in Version 1 -
      see "Future Relationship" above.
    - This module depends only on argus.decision.status
      (DecisionRecordStatus), argus.decision.priority
      (DecisionRecordPriority), and argus.decision.metadata
      (DecisionRecordMetadata) to type its own fields. It has no
      dependency on argus.decision.decision, argus.decision.engine,
      or argus.decision.rule - this module is a fully independent
      leaf from Package 021's own Decision Engine, sharing only the
      package directory.

Dependencies:
    argus.decision.status (DecisionRecordStatus),
    argus.decision.priority (DecisionRecordPriority),
    argus.decision.metadata (DecisionRecordMetadata).
"""

import uuid
from dataclasses import dataclass, field

from argus.decision.metadata import DecisionRecordMetadata
from argus.decision.priority import DecisionRecordPriority
from argus.decision.status import DecisionRecordStatus


@dataclass(frozen=True)
class DecisionRecord:
    """
    An immutable record of one captured decision - a question, the
    outcome selected, and the current status/priority of that
    decision. See the module docstring for the full field semantics
    and for why this class is named DecisionRecord rather than
    Decision.

    Fields:
        decision_id: Unique identifier for this DecisionRecord.
            Defaults to a fresh uuid4 string.
        title: A short, human-readable label for this DecisionRecord.
            Defaults to an empty string.
        question: The question this DecisionRecord captures. Defaults
            to an empty string.
        status: This DecisionRecord's current DecisionRecordStatus.
            Defaults to DecisionRecordStatus.PENDING.
        priority: This DecisionRecord's current DecisionRecordPriority.
            Defaults to DecisionRecordPriority.NORMAL.
        metadata: Descriptive bookkeeping about this DecisionRecord.
            Defaults to a fresh DecisionRecordMetadata.
    """

    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    question: str = ""
    status: DecisionRecordStatus = DecisionRecordStatus.PENDING
    priority: DecisionRecordPriority = DecisionRecordPriority.NORMAL
    metadata: DecisionRecordMetadata = field(default_factory=DecisionRecordMetadata)
