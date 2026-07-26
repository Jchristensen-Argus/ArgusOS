"""
The DecisionRule value object for the ArgusOS Decision Engine.

Purpose:
    Represent a single, immutable, deterministic evaluation rule - a
    name, description, priority, and a plain Python predicate - per
    factory/packages/021_DECISION_ENGINE.md. A DecisionRule is pure
    data: it does not evaluate itself, register itself, or know
    whether it currently matches anything. DecisionEngine (argus/
    decision/engine.py) is the only component that calls a rule's
    `predicate` and interprets the result.

No Scripting, No Python Execution, No Dynamic Code Generation:
    `predicate` is a plain Python callable, supplied directly by the
    caller at construction time - never a string of code, a DSL
    expression, or any other data this module or DecisionEngine
    parses, `eval()`s, `exec()`s, or dynamically compiles. This
    package implements no interpreter or scripting language of any
    kind: the caller's own Python function IS the rule; DecisionRule
    and DecisionEngine only store it and call it, deterministically,
    in priority order. This satisfies this package's own explicit
    "No scripting. No Python execution. No dynamic code generation"
    constraint by construction, not by added validation - there is
    no code path anywhere in this package capable of executing
    arbitrary text as code in the first place.

Naming Note:
    `id`, not `rule_id`, for this model's own identity field - the
    same established convention already applied to `Entity.id`,
    `Relationship.id`, `Connector.id`, and every other value object in
    this codebase (see entity.py's own Naming Note for the fullest
    statement of this precedent). The Decision Engine's own public
    methods use `rule_id` for the parameter name that refers to it.

Priority Ordering:
    Lower `priority` values are evaluated first ("priority 0" runs
    before "priority 10"). Ties are broken by registration order,
    deterministically - see DecisionEngine.list_rules()'s own
    docstring.

Responsibilities:
    - DecisionRule: hold rule identity, metadata, and a predicate
      callable as an immutable value object.

Non-Responsibilities:
    - DecisionRule does not register, remove, or evaluate itself -
      see argus.decision.interfaces.IDecisionEngine and
      argus.decision.engine.DecisionEngine.
    - This module has no dependency on any other argus.decision
      module, matching the "pure, dependency-free leaf" precedent set
      by every other value object in this codebase. It does depend on
      argus.reasoning.result.ReasoningResult, solely to type the
      `predicate` field's expected signature - the same category of
      cross-package typing dependency ReasoningResult itself has on
      argus.knowledge_graph's Entity/Relationship.

Dependencies:
    argus.reasoning.result (ReasoningResult), for typing only.
"""

import uuid
from dataclasses import dataclass, field
from typing import Callable, Sequence

from argus.reasoning.result import ReasoningResult

#: A rule's predicate: given the full sequence of ReasoningResult
#: objects being evaluated, deterministically return whether this
#: rule matches.
DecisionPredicate = Callable[[Sequence[ReasoningResult]], bool]


@dataclass(frozen=True)
class DecisionRule:
    """
    An immutable, deterministic evaluation rule for the Decision
    Engine.

    Fields:
        name: Human-readable name. Required, non-empty. Not enforced
            unique - lookup is always by `id`, never by `name`,
            matching every other registry in this codebase.
        predicate: A plain Python callable,
            `Callable[[Sequence[ReasoningResult]], bool]`. Required.
            See the module docstring's "No Scripting" note.
        priority: This rule's evaluation order, lower first. Defaults
            to 0.
        id: Unique identifier for this DecisionRule. Defaults to a
            fresh uuid4 string.
        description: Human-readable explanation of what this rule
            checks for. Defaults to an empty string.
    """

    name: str
    predicate: DecisionPredicate
    priority: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
