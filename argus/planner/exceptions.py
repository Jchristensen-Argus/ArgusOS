"""
Exceptions raised by the ArgusOS Planner.

Purpose:
    Give callers explicit, catchable failure modes for plan creation,
    mutation, and validation, per the coding standard's "raise
    meaningful exceptions... never silently ignore errors" and
    factory/packages/015_PLANNER.md. Mirrors the exception hierarchy
    shape already established by argus.plugins.exceptions (Package
    014), argus.capability.exceptions (Package 013), and
    argus.workflow.exceptions (Package 010).

Responsibilities:
    - Provide a general planner-subsystem error base, and more
      specific subtypes for "invalid plan/step," "not found," and
      "validation failed" failures.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do
      not log, retry, or recover.

Dependencies:
    None.
"""


class PlannerError(Exception):
    """Base exception for the planner subsystem. Raised directly for
    failures that are not one of the more specific subtypes below."""


class InvalidPlanError(PlannerError):
    """Raised when create_plan() is given something that is not an
    Intent instance, when add_step() is given an empty description or
    empty required_capability, when reorder_steps() is given a
    sequence that is not an exact permutation of the plan's current
    step ids, or when any method is given something that is not the
    expected type (a non-string plan_id, a non-string step_id)."""


class PlanNotFoundError(PlannerError):
    """Raised when get_plan(), add_step(), remove_step(),
    reorder_steps(), or validate_plan() references a plan_id with no
    corresponding registered Plan."""


class StepNotFoundError(PlannerError):
    """Raised when remove_step() references a step_id with no
    corresponding step in the referenced Plan."""


class PlanValidationError(PlannerError):
    """Raised by validate_plan() when a non-optional PlanStep's
    required_capability is not registered with the Capability
    Registry. The Plan itself is still persisted with
    PlanStatus.FAILED - callers may inspect get_plan() afterward to
    see which validation last failed and why."""
