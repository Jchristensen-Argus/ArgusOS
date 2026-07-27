"""
Planner: in-memory, reasoning-only implementation of IPlanner for the
ArgusOS Planner.

Purpose:
    Implement IPlanner: convert an Intent into an ordered Execution
    Plan, and let callers inspect, mutate, and validate it, per
    factory/packages/015_PLANNER.md. The Planner performs reasoning
    only - it never executes a workflow, never dispatches an action,
    and never calls a plugin. Execution remains entirely outside this
    package, per this package's explicit Objective. Also implements
    plan_session(), a second, additive entry point that builds a Plan
    from a PlanningSession by delegating to the exact same
    create_plan()/add_step() methods below, per
    factory/packages/024_PLANNER_SESSION_INTEGRATION.md - see this
    module's own "plan_session()" section further down.

Package 030 Amendment - Plans Can Contain Tasks:
    "Update Planner so that Plans can contain Tasks. Do not generate
    tasks automatically. The Planner simply preserves whatever Tasks
    are supplied during construction. No planning logic changes. No
    AI. No decomposition." create_plan() gained one new optional
    keyword parameter, `tasks: Optional[Sequence[Task]] = None`,
    validated by the new _validate_tasks() helper (isinstance checks
    plus duplicate-`task_id` rejection - "no duplicates," Package
    030's own explicit Plan requirement) and stored on the constructed
    Plan unchanged - no step is generated from a Task, no Task is
    generated from a step, and no existing planning behavior (goal-
    to-step mapping, constraint-to-metadata mapping, validation) is
    touched. plan_session() was amended identically to how it already
    carries `constraints` through onto `Plan.metadata` (Package 024):
    it now also passes `tasks=planning_session.tasks` straight through
    to create_plan(), so a Plan built from a PlanningSession carries
    forward whatever Tasks that session already held - itself either
    empty, or populated via PlanningSessionBuilder.with_task()/
    with_tasks() (argus.planning.builder, Package 030's own other
    amendment).

Responsibilities:
    - create_plan / add_step / remove_step / reorder_steps /
      validate_plan / get_plan / list_plans: an in-memory registry of
      Plan objects, keyed by id. All seven methods are always
      available - Planner is not an IService adopter (see
      argus/planner/interfaces.py's Architectural Note), so there is
      no lifecycle state to gate any of them on.
    - Every mutation constructs a new Plan (and, where steps change,
      new PlanStep instances with recomputed `order` fields) via
      dataclasses.replace, and stores it under the same id - Plan and
      PlanStep are both frozen, matching the precedent set by
      WorkflowEngine's own treatment of Workflow (Package 010) and
      PluginManager's treatment of Plugin (Package 014): mutation
      happens by replacement, never by attribute assignment.
    - Any structural mutation (add_step(), remove_step(),
      reorder_steps()) resets the Plan's status to
      PlanStatus.CREATED, even if it was previously VALIDATED or
      FAILED. This is a deliberate business rule, not specified
      verbatim by the work order: a Plan's VALIDATED/FAILED status
      describes whether its *current* steps were last confirmed
      against the Capability Registry, so changing those steps
      without re-validating would let a stale, no-longer-accurate
      status persist. Re-running validate_plan() is always required
      after any structural change.
    - validate_plan() checks only that every non-optional PlanStep's
      required_capability is currently registered with the injected
      ICapabilityRegistry (via `contains()`) - it never calls `get()`,
      never inspects a Capability's own `enabled` flag, and never
      invokes anything the Capability Registry describes. A Plan with
      no steps validates successfully (vacuously true).

plan_session() - Delegation, Not A Second Algorithm (Package 024):
    plan_session(planning_session) does exactly three things, in
    order, and nothing else: (1) synthesize an Intent from the
    session (PlanningSession carries no Intent of its own anywhere in
    its structure - see _synthesize_intent()'s own docstring), (2)
    call self.create_plan() with that Intent, and (3) call
    self.add_step() once per planning_session.goal, in order. Every
    event this produces (PLAN_CREATED, one PLAN_UPDATED per goal) is
    published by create_plan()/add_step() themselves, exactly as it
    would be for any other caller of those two methods -
    plan_session() itself publishes nothing directly. This is what
    "No duplicate planning logic" means concretely: there is no
    second, parallel implementation of "how a Plan gets built," only
    a second, higher-level way to invoke the one that already existed.

Goal-to-Step and Constraint-to-Metadata Mapping (Package 024):
    Each PlanningGoal becomes one PlanStep: `description` is the
    goal's own `description` if non-empty, else its `name` (PlanStep
    .description must be a non-empty string per add_step()'s own
    validation, but PlanningGoal.description defaults to ""); `
    required_capability` is the goal's `name` - PlanningGoal has no
    field more specifically analogous to "which Capability satisfies
    this," so its one other identifying string field is the most
    direct, deterministic choice, the same category of "derive an id
    from an existing field rather than inventing new state" resolution
    Package 019's MemoryMapper (f"memory:{key}") and Package 016's
    synthetic-Intent-per-step both used for a related problem. `order`
    is assigned by add_step() itself, exactly as it always is.
    `optional` defaults to False, matching add_step()'s own default -
    PlanningGoal carries no equivalent concept. `metadata` carries the
    goal's own `goal_id` and `priority`, so neither is silently
    dropped even though neither has a direct PlanStep field.
    PlanningConstraints are never turned into PlanSteps at all - a
    constraint describes a limit, not an action to take, which is not
    what a PlanStep represents - instead, every constraint's
    `constraint_id`/`name`/`description` is recorded as a plain,
    descriptive list under the created Plan's own
    `metadata["constraints"]`, alongside `metadata
    ["planning_session_id"]` (always present) and
    `metadata["cognitive_context_id"]` (present only when
    planning_session.cognitive_context is not None). A session with no
    goals and no constraints produces a Plan with zero steps and an
    empty `constraints` list in its metadata - the same "vacuously
    fine, nothing to check" treatment validate_plan() already gives an
    empty Plan.

Capability Integration:
    The one and only touchpoint with the Capability Registry is
    validate_plan()'s read-only `ICapabilityRegistry.contains()` call.
    Planner never calls `register()`, `unregister()`, `get()`, or
    `find_by_intent_type()` - it only asks "does a Capability with
    this id currently exist?" and never constructs, obtains, or
    invokes one. No change was made to argus/capability/ to support
    this - `contains()` already existed, unchanged, since Package 013.

Non-Responsibilities:
    - Planner never executes a Plan, never dispatches an Intent, and
      never calls a plugin - it has no dependency on
      argus.dispatcher, argus.workflow, or argus.plugins anywhere in
      this module, per this package's explicit Objective and Plugin
      Integration guidance ("The Planner should remain completely
      unaware of plugins").
    - Planner does not optimize plans (no reordering heuristic, no
      redundant-step detection) and does not schedule plans (no
      timing, no recurrence) - both explicitly out of Version 1
      scope, reserved for future packages.
    - No AI, no LLM, no networking, no persistence - Plans are held
      only in memory, exactly like CapabilityRegistry's Capabilities
      and PluginManager's Plugins.
    - plan_session() never modifies the PlanningSession it is given,
      or that session's own cognitive_context, goals, or constraints -
      every one of those is already an immutable value object
      (Packages 022/023), so this is true by construction, not by
      anything this module does to enforce it. plan_session() imports
      only argus.planning.session.PlanningSession - never
      argus.planning.builder, argus.planning.metadata, or
      argus.planning.exceptions, per this package's own explicit
      Dependency Rules.

Dependencies:
    argus.planner (Plan, PlanStatus, PlanStep, IPlanner, and the
    planner exceptions), argus.capability.interfaces (ICapabilityRegistry,
    for validate_plan()'s read-only existence check only),
    argus.intent.intent (Intent), argus.events (Event, EventType,
    IEventBus), argus.planning.session (PlanningSession) - Package
    024, the immutable contract only, for plan_session() -
    argus.task.task (Task) - Package 030, the immutable contract
    only, for create_plan()'s own tasks parameter.
"""

import dataclasses
from typing import Any, Dict, List, Optional, Sequence, Tuple

from argus.capability.interfaces import ICapabilityRegistry
from argus.events.event import Event
from argus.events.event_types import EventType
from argus.events.interfaces import IEventBus
from argus.intent.intent import Intent, IntentType
from argus.planner.exceptions import (
    InvalidPlanError,
    PlanNotFoundError,
    PlanValidationError,
    StepNotFoundError,
)
from argus.planner.interfaces import IPlanner
from argus.planner.plan import Plan, PlanStatus
from argus.planner.step import PlanStep
from argus.planning.session import PlanningSession
from argus.task.task import Task


class Planner(IPlanner):
    """
    In-memory implementation of IPlanner.

    Purpose:
        Be the sole place ArgusOS converts an Intent into an ordered,
        inspectable Execution Plan, as reasoning only - no execution,
        no dispatch, no plugin awareness. See the module docstring for
        the full design rationale.

    Dependencies:
        An IEventBus implementation and an ICapabilityRegistry
        implementation, both injected by the caller (bootstrap.py).
    """

    def __init__(self, event_bus: IEventBus, capability_registry: ICapabilityRegistry) -> None:
        self._event_bus = event_bus
        self._capability_registry = capability_registry
        self._plans: Dict[str, Plan] = {}

    def plan_session(self, planning_session: PlanningSession) -> Plan:
        if not isinstance(planning_session, PlanningSession):
            raise InvalidPlanError(
                f"plan_session() requires a PlanningSession, got {planning_session!r}."
            )
        intent = self._synthesize_intent_for_session(planning_session)
        plan = self.create_plan(
            intent,
            metadata=self._session_plan_metadata(planning_session),
            tasks=planning_session.tasks,
        )
        for goal in planning_session.goals:
            plan = self.add_step(
                plan.id,
                description=goal.description or goal.name,
                required_capability=goal.name,
                metadata={"goal_id": goal.goal_id, "priority": goal.priority},
            )
        return plan

    def create_plan(
        self,
        intent: Intent,
        *,
        metadata: Optional[dict] = None,
        tasks: Optional[Sequence[Task]] = None,
    ) -> Plan:
        if not isinstance(intent, Intent):
            raise InvalidPlanError(f"create_plan() requires an Intent, got {intent!r}.")
        plan = Plan(
            originating_intent=intent,
            metadata=metadata or {},
            tasks=self._validate_tasks(tasks),
        )
        self._plans[plan.id] = plan
        self._publish(EventType.PLAN_CREATED, {"plan_id": plan.id})
        return plan

    def add_step(
        self,
        plan_id: str,
        *,
        description: str,
        required_capability: str,
        optional: bool = False,
        metadata: Optional[dict] = None,
    ) -> Plan:
        plan = self._require_plan(plan_id)
        if not isinstance(description, str) or not description:
            raise InvalidPlanError("PlanStep.description must be a non-empty string.")
        if not isinstance(required_capability, str) or not required_capability:
            raise InvalidPlanError(
                "PlanStep.required_capability must be a non-empty string."
            )
        step = PlanStep(
            description=description,
            required_capability=required_capability,
            order=len(plan.steps),
            optional=optional,
            metadata=metadata or {},
        )
        updated = dataclasses.replace(
            plan, steps=plan.steps + (step,), status=PlanStatus.CREATED
        )
        self._plans[plan_id] = updated
        self._publish(
            EventType.PLAN_UPDATED,
            {"plan_id": plan_id, "change": "added_step", "step_id": step.id},
        )
        return updated

    def remove_step(self, plan_id: str, step_id: str) -> Plan:
        plan = self._require_plan(plan_id)
        if not isinstance(step_id, str):
            raise InvalidPlanError(f"step_id must be a string, got {step_id!r}.")
        if not any(step.id == step_id for step in plan.steps):
            raise StepNotFoundError(
                f"No step with id {step_id!r} in plan {plan_id!r}."
            )
        remaining = [step for step in plan.steps if step.id != step_id]
        renumbered = tuple(
            dataclasses.replace(step, order=index)
            for index, step in enumerate(remaining)
        )
        updated = dataclasses.replace(plan, steps=renumbered, status=PlanStatus.CREATED)
        self._plans[plan_id] = updated
        self._publish(
            EventType.PLAN_UPDATED,
            {"plan_id": plan_id, "change": "removed_step", "step_id": step_id},
        )
        return updated

    def reorder_steps(self, plan_id: str, step_ids: Sequence[str]) -> Plan:
        plan = self._require_plan(plan_id)
        by_id = {step.id: step for step in plan.steps}
        candidate: List[str] = list(step_ids) if isinstance(step_ids, (list, tuple)) else []
        if (
            not isinstance(step_ids, (list, tuple))
            or len(candidate) != len(by_id)
            or len(set(candidate)) != len(candidate)
            or set(candidate) != set(by_id.keys())
        ):
            raise InvalidPlanError(
                "reorder_steps() requires step_ids to be an exact permutation of "
                "the plan's current step ids."
            )
        reordered = tuple(
            dataclasses.replace(by_id[step_id], order=index)
            for index, step_id in enumerate(candidate)
        )
        updated = dataclasses.replace(plan, steps=reordered, status=PlanStatus.CREATED)
        self._plans[plan_id] = updated
        self._publish(
            EventType.PLAN_UPDATED, {"plan_id": plan_id, "change": "reordered"}
        )
        return updated

    def validate_plan(self, plan_id: str) -> Plan:
        plan = self._require_plan(plan_id)
        missing = [
            step
            for step in plan.steps
            if not step.optional
            and not self._capability_registry.contains(step.required_capability)
        ]
        if missing:
            failed = dataclasses.replace(plan, status=PlanStatus.FAILED)
            self._plans[plan_id] = failed
            missing_ids = [step.required_capability for step in missing]
            raise PlanValidationError(
                f"Plan {plan_id!r} failed validation: required capability id(s) "
                f"{missing_ids!r} are not registered with the Capability Registry."
            )
        validated = dataclasses.replace(plan, status=PlanStatus.VALIDATED)
        self._plans[plan_id] = validated
        self._publish(EventType.PLAN_VALIDATED, {"plan_id": plan_id})
        return validated

    def get_plan(self, plan_id: str) -> Plan:
        return self._require_plan(plan_id)

    def list_plans(self) -> Sequence[Plan]:
        return tuple(self._plans.values())

    # -- internals ------------------------------------------------------

    def _synthesize_intent_for_session(self, planning_session: PlanningSession) -> Intent:
        # PlanningSession carries no Intent anywhere in its own
        # structure (nor does the CognitiveContext it holds) - there
        # is nothing here to classify, so this deliberately uses
        # IntentType.UNKNOWN with confidence=0.0 rather than fabricate
        # a classification the session never actually contained,
        # matching Intent's own "Unrecognized input always classifies
        # as UNKNOWN" precedent. The session's own session_id (and,
        # when present, its cognitive_context's context_id) are
        # carried through in `parameters` for traceability, the same
        # "pass real identifying data through an existing field"
        # approach Package 016's own synthetic-Intent-per-step
        # solution used.
        parameters: Dict[str, Any] = {"planning_session_id": planning_session.session_id}
        if planning_session.cognitive_context is not None:
            parameters["cognitive_context_id"] = planning_session.cognitive_context.context_id
        return Intent(name=IntentType.UNKNOWN, confidence=0.0, parameters=parameters)

    def _session_plan_metadata(self, planning_session: PlanningSession) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {"planning_session_id": planning_session.session_id}
        if planning_session.cognitive_context is not None:
            metadata["cognitive_context_id"] = planning_session.cognitive_context.context_id
        metadata["constraints"] = tuple(
            {
                "constraint_id": constraint.constraint_id,
                "name": constraint.name,
                "description": constraint.description,
            }
            for constraint in planning_session.constraints
        )
        return metadata

    def _validate_tasks(self, tasks: Optional[Sequence[Task]]) -> Tuple[Task, ...]:
        # "no duplicates" (Package 030's own explicit Plan
        # requirement) - enforced here, on the Plan side, mirroring
        # PlanningSessionBuilder.with_task()'s own identical check on
        # the PlanningSession side (argus.planning.builder). Plan
        # itself performs no validation of its own - see plan.py's
        # own module docstring.
        if tasks is None:
            return ()
        if not isinstance(tasks, (list, tuple)):
            raise InvalidPlanError(
                f"tasks must be a list or tuple of Task instances, got {tasks!r}."
            )
        seen_ids = set()
        validated: List[Task] = []
        for task in tasks:
            if not isinstance(task, Task):
                raise InvalidPlanError(
                    f"tasks must contain only Task instances, got {task!r}."
                )
            if task.task_id in seen_ids:
                raise InvalidPlanError(
                    f"Duplicate task_id {task.task_id!r} in tasks."
                )
            seen_ids.add(task.task_id)
            validated.append(task)
        return tuple(validated)

    def _require_plan(self, plan_id: str) -> Plan:
        if not isinstance(plan_id, str):
            raise InvalidPlanError(f"plan_id must be a string, got {plan_id!r}.")
        try:
            return self._plans[plan_id]
        except KeyError:
            raise PlanNotFoundError(f"No plan registered with id {plan_id!r}.") from None

    def _publish(self, event_type: EventType, payload: dict) -> None:
        self._event_bus.publish(
            Event(type=event_type, source="planner", payload=payload)
        )
