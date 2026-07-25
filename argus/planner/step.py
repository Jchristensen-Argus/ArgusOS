"""
The PlanStep value object for the ArgusOS Planner.

Purpose:
    Represent a single, immutable, ordered unit of work within a Plan
    - a planning-time description of "one thing that needs to happen"
    and the Capability it requires, per
    factory/packages/015_PLANNER.md. A PlanStep is pure data: it does
    not execute anything, does not resolve or invoke its
    required_capability, and does not know which Action or Workflow
    will eventually realize it - the Planner never dispatches actions
    or calls plugins, per this package's explicit Objective.

Responsibilities:
    - Hold identity (id), a human-readable description, the id of the
      Capability this step requires (required_capability), this
      step's position within its Plan (order), whether the step is
      optional (optional - see Non-Responsibilities), and arbitrary
      caller metadata.
    - Auto-generate `id` when not supplied. Guarantee immutability
      (frozen dataclass) and prevent mutation of the `metadata`
      mapping after construction.

Non-Responsibilities:
    - PlanStep does not validate its own fields (for example, that
      description or required_capability is non-empty) - that is
      Planner.add_step()'s responsibility, matching the validation
      precedent set by Capability/Plugin/Workflow: data objects
      across this codebase contain no business logic.
    - PlanStep does not check whether required_capability actually
      exists in the Capability Registry - that is
      Planner.validate_plan()'s responsibility. A PlanStep with
      optional=True is not required to have an existing
      required_capability for its Plan to pass validation (see
      Planner.validate_plan()'s docstring); optional=False (the
      default) means validation fails if required_capability is not
      registered.
    - `order` is maintained exclusively by Planner (via add_step(),
      remove_step(), and reorder_steps()) to always match the step's
      actual position within its Plan's `steps` tuple - a PlanStep
      never reassigns its own `order`, and no public Planner method
      lets a caller set it directly, avoiding the two-independent-
      trackers-of-the-same-fact risk this codebase has been careful
      about since ADR-0002.

Dependencies:
    None (standard library only).
"""

import uuid
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class PlanStep:
    """
    An immutable record describing one ordered unit of work within a
    Plan.

    Purpose:
        Let the Planner describe "what needs to happen and in what
        order" as pure planning data, without executing, dispatching,
        or invoking anything - see the module docstring.

    Responsibilities:
        - Store description, required_capability, id, order,
          optional, and metadata.
        - Auto-generate `id` when not supplied, default `order` to 0
          and `optional` to False, and make `metadata` an immutable
          container.

    Dependencies:
        None.
    """

    description: str
    required_capability: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order: int = 0
    optional: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Frozen dataclasses require object.__setattr__ during
        # __post_init__. Wrapping `metadata` in MappingProxyType makes
        # the container itself read-only, not just the attribute
        # reference - the same pattern used by Capability.metadata
        # (Package 013) and Plugin.metadata (Package 014).
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
