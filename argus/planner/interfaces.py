"""
Public interface contract for the ArgusOS Planner.

Purpose:
    Define IPlanner, the contract other modules depend on, per
    factory/packages/015_PLANNER.md and
    factory/packages/024_PLANNER_SESSION_INTEGRATION.md.

Architectural Note - Why IPlanner Does NOT Inherit IService:
    Unlike Scheduler, IntentRouter, WorkflowEngine, ConversationManager,
    and IntentDispatcher (Packages 008-012), Planner has no genuine
    multi-phase behavior: create_plan/validate_plan/add_step/
    remove_step/reorder_steps/get_plan/list_plans are all fully usable
    the instant the Planner is constructed, with no background
    thread, no connection to open or close, and nothing meaningful for
    start()/stop() to enable or disable. Planner performs reasoning
    only - it never executes a plan, never dispatches an action, and
    never calls a plugin, per this package's explicit Objective - so
    there is no "active work" phase for start()/stop() to gate, the
    same reasoning that already applied to Capability Registry
    (Package 013) and Plugin Manager (Package 014). Per ADR-0002's
    proposed criterion ("adopt IService only when start()/stop()
    would do real, distinct work"), this is architecturally identical
    to Knowledge Service (006), Memory Service (007), Capability
    Registry (013), and Plugin Manager (014) - see
    design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md's Empirical
    Finding for this package. Planner is registered with the
    Lifecycle Manager as LifecycleState.REGISTERED only, exactly like
    those four, not as a fully-lifecycled IService adopter.

Architectural Note - plan_session() Is An Additional Entry Point,
Not A Replacement (Package 024):
    "The Planner shall now recognize PlanningSession as a first-class
    input... This package introduces an additional interface - not a
    replacement." `plan_session()` is a second, higher-level way to
    reach the exact same planning logic `create_plan()`/`add_step()`
    already provide - it extracts the required information from a
    `PlanningSession` and internally delegates to those same two
    methods, rather than reimplementing anything. "No duplicate
    planning logic." Every pre-existing IPlanner method - including
    `create_plan()` itself - continues to function exactly as it did
    before this package; `plan_session()` is purely additive. See
    argus.planner.planner.Planner's own module docstring for the full
    goal-to-step and constraint-to-metadata mapping this method
    applies, and factory/packages/024_PLANNER_SESSION_INTEGRATION.md
    for the complete architectural rationale.

Architectural Note - Dependency Boundary: PlanningSession Only, Not
Builder/Metadata/Exceptions (Package 024):
    Per this package's own explicit Dependency Rules, this module
    imports only `argus.planning.session.PlanningSession` - never
    `argus.planning.builder`, `argus.planning.metadata`, or
    `argus.planning.exceptions`. `plan_session()` raises this
    package's own pre-existing `InvalidPlanError` for malformed input,
    exactly the same exception `create_plan()` already raises for a
    non-`Intent` argument - no new exception type was introduced, and
    none of `argus.planning`'s own exception types are ever caught,
    raised, or referenced here. "Use only the immutable contract."

Responsibilities:
    - IPlanner: create_plan / validate_plan / add_step / remove_step /
      reorder_steps / get_plan / list_plans.

Non-Responsibilities:
    - This module implements no behavior; see
      argus.planner.planner.Planner.
    - IPlanner does not execute plans, dispatch intents, invoke
      capabilities, or call plugins - see this package's
      Architectural Guidance and argus.dispatcher.dispatcher.
      IntentDispatcher / argus.workflow.engine.WorkflowEngine for
      those responsibilities.

Dependencies:
    argus.planner.plan (Plan), argus.planner.step (PlanStep),
    argus.intent.intent (Intent),
    argus.planning.session (PlanningSession) - Package 024, the
    immutable contract only (see this module's own Architectural
    Note).
"""

from abc import ABC, abstractmethod
from typing import Optional, Sequence

from argus.intent.intent import Intent
from argus.planner.plan import Plan
from argus.planning.session import PlanningSession


class IPlanner(ABC):
    """
    Reasoning-only contract for converting an Intent into an ordered
    Execution Plan.

    Purpose:
        Let callers create, inspect, mutate, and validate Plans
        without the Planner itself executing anything, dispatching
        intents, or calling plugins - see this module's Architectural
        Note for why this interface is a plain ABC rather than an
        IService.
    """

    @abstractmethod
    def plan_session(self, planning_session: PlanningSession) -> Plan:
        """Create and populate a Plan from a PlanningSession, by
        internally delegating to create_plan()/add_step() - no
        duplicate planning logic. Each of planning_session.goals
        becomes one PlanStep (see planner.py's own module
        docstring for the exact mapping);
        planning_session.constraints are recorded descriptively in
        the returned Plan's own metadata, never as steps. Never
        modifies planning_session, its cognitive_context, its goals,
        or its constraints - every one of those is already an
        immutable value object, so this is true by construction, not
        by added policy. Raises InvalidPlanError if planning_session
        is not a PlanningSession instance. See this module's own
        Architectural Notes for why this is an additional entry point
        rather than a replacement, and why this method's only
        argus.planning dependency is PlanningSession itself."""

    @abstractmethod
    def create_plan(self, intent: Intent, *, metadata: Optional[dict] = None) -> Plan:
        """Create and store a new, empty Plan (PlanStatus.CREATED,
        no steps) for `intent`. Raises InvalidPlanError if intent is
        not an Intent instance."""

    @abstractmethod
    def add_step(
        self,
        plan_id: str,
        *,
        description: str,
        required_capability: str,
        optional: bool = False,
        metadata: Optional[dict] = None,
    ) -> Plan:
        """Append a new PlanStep (ordered after every existing step)
        to the Plan registered under plan_id, and return the updated
        Plan. Raises InvalidPlanError if plan_id is not a string, or
        if description or required_capability is empty. Raises
        PlanNotFoundError if plan_id has no registered Plan. Resets
        the Plan's status to PlanStatus.CREATED, per this package's
        "a structural mutation invalidates any prior validation"
        rule - see Planner's module docstring."""

    @abstractmethod
    def remove_step(self, plan_id: str, step_id: str) -> Plan:
        """Remove the PlanStep identified by step_id from the Plan
        registered under plan_id, renumber the remaining steps'
        `order` fields to stay contiguous, and return the updated
        Plan. Raises InvalidPlanError if plan_id or step_id is not a
        string. Raises PlanNotFoundError if plan_id has no registered
        Plan. Raises StepNotFoundError if step_id has no corresponding
        step in that Plan. Resets the Plan's status to
        PlanStatus.CREATED."""

    @abstractmethod
    def reorder_steps(self, plan_id: str, step_ids: Sequence[str]) -> Plan:
        """Reorder the Plan registered under plan_id so its steps
        appear in the order given by step_ids, reassigning each
        step's `order` field to match, and return the updated Plan.
        Raises InvalidPlanError if plan_id is not a string, or if
        step_ids is not an exact permutation of the Plan's current
        step ids (same set, same length, no duplicates). Raises
        PlanNotFoundError if plan_id has no registered Plan. Resets
        the Plan's status to PlanStatus.CREATED."""

    @abstractmethod
    def validate_plan(self, plan_id: str) -> Plan:
        """Validate the Plan registered under plan_id: for every
        PlanStep with optional=False, verify that step's
        required_capability is currently registered with the
        Capability Registry (via ICapabilityRegistry.contains()) -
        never invoking it. On success, store and return the Plan with
        status=PlanStatus.VALIDATED. On failure (a non-optional
        step's required_capability is not registered), store the Plan
        with status=PlanStatus.FAILED and raise PlanValidationError -
        callers may inspect get_plan(plan_id) afterward to see the
        persisted failure. Raises InvalidPlanError if plan_id is not a
        string. Raises PlanNotFoundError if plan_id has no registered
        Plan. A Plan with no steps at all validates successfully
        (vacuously true - nothing to check)."""

    @abstractmethod
    def get_plan(self, plan_id: str) -> Plan:
        """Return the Plan registered under plan_id. Raises
        InvalidPlanError if plan_id is not a string. Raises
        PlanNotFoundError if plan_id has no registered Plan."""

    @abstractmethod
    def list_plans(self) -> Sequence[Plan]:
        """Return every registered Plan, in creation order."""
