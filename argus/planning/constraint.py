"""
The PlanningConstraint value object for the ArgusOS Planning Session.

Purpose:
    Represent a single, immutable, descriptive planning constraint a
    PlanningSession carries - a name, description, and arbitrary
    metadata - per factory/packages/023_PLANNING_SESSION.md. A
    PlanningConstraint is pure data: it does not enforce itself,
    evaluate whether anything satisfies it, or know which
    PlanningSession (if any) it belongs to.

No Validation Logic:
    "No validation logic." Unlike `DecisionRule.predicate` (Package
    021), which is an executable callable `DecisionEngine` invokes,
    `PlanningConstraint` carries no callable, expression, or any other
    mechanism capable of being evaluated against anything - it is
    purely descriptive data a future package may choose to interpret,
    once the Planner is instructed to consume PlanningSession (Version
    1 explicitly does not). This package implements no constraint
    engine of any kind.

Field Ordering Note:
    The work order lists this model's fields in "constraint_id, name,
    description, metadata" order. `name` has no sensible default (an
    unnamed constraint is not a meaningful constraint), so it must
    precede the defaulted fields in this dataclass's own declaration
    order - reordered to "name, constraint_id, description, metadata"
    here, the same "required fields before defaulted fields"
    reordering already applied to `Entity`, `ReasoningQuery`, and
    `DecisionRule` before it. The work order's own listed order is
    preserved in this docstring's Fields list below, for readability.

No Validation Here - See builder.py:
    Like every other value object in this codebase, PlanningConstraint
    performs no validation of its own fields in __post_init__ beyond
    the standard mutable-to-immutable wrapping (dict ->
    MappingProxyType). PlanningSessionBuilder (builder.py) validates a
    PlanningConstraint before accumulating it - see builder.py's own
    module docstring.

Responsibilities:
    - PlanningConstraint: hold constraint identity, a human-readable
      name and description, and arbitrary descriptive metadata as an
      immutable value object.

Non-Responsibilities:
    - PlanningConstraint does not register, remove, or evaluate
      itself against anything - see
      argus.planning.session.PlanningSession and
      argus.planning.builder.PlanningSessionBuilder.
    - This module has no dependency on any other argus.planning
      module, matching the "pure, dependency-free leaf" precedent set
      by every other value object in this codebase.

Dependencies:
    None.
"""

import uuid
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class PlanningConstraint:
    """
    An immutable, descriptive planning constraint. See the module
    docstring for the full field semantics.

    Fields:
        name: Human-readable name. Required, non-empty (not enforced
            here - see builder.py). Not enforced unique - lookup is
            always by `constraint_id`, matching every other
            identity-bearing value object in this codebase.
        constraint_id: Unique identifier for this PlanningConstraint.
            Defaults to a fresh uuid4 string.
        description: Human-readable explanation of what this
            constraint is. Defaults to an empty string.
        metadata: Additional descriptive data about this constraint.
            Defaults to an empty mapping.
    """

    name: str
    constraint_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
