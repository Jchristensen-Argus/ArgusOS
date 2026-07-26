"""
Exceptions raised by the ArgusOS Planning Session package.

Purpose:
    Give callers explicit, catchable failure modes for invalid
    PlanningSessionBuilder input, per the coding standard's "raise
    meaningful exceptions... never silently ignore errors" and
    factory/packages/023_PLANNING_SESSION.md. Mirrors the minimal
    exception hierarchy shape already established by
    argus.context.exceptions (Package 022) - a single base plus one
    narrow, specific subtype.

Responsibilities:
    - Provide a general Planning Session error base, and a more
      specific subtype for invalid PlanningSessionBuilder input.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do
      not log, retry, or recover.
    - No lifecycle-state exception exists here, and PlanningError is
      never raised for that reason - PlanningSession and
      PlanningSessionBuilder are plain value objects with no IService
      lifecycle at all (see interfaces.py's own Architectural Note
      for why this package introduces no new core service).

Dependencies:
    None.
"""


class PlanningError(Exception):
    """Base exception for the Planning Session package."""


class InvalidPlanningSessionError(PlanningError):
    """Raised when a PlanningSessionBuilder `with_*` method is given
    malformed input: a non-CognitiveContext passed to with_context(),
    a non-PlanningGoal item passed to with_goal(), a non-
    PlanningConstraint item passed to with_constraint(), or a
    non-string/empty metadata key passed to with_metadata().
    PlanningSession, PlanningGoal, and PlanningConstraint themselves
    perform no validation - see each module's own docstring - so this
    is only ever raised by PlanningSessionBuilder."""
