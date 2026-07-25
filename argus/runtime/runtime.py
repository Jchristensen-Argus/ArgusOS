"""
AgentRuntime: in-memory, synchronous implementation of IAgentRuntime
for the ArgusOS Agent Runtime.

Purpose:
    Implement IAgentRuntime: execute an already-validated Plan by
    dispatching its PlanSteps, in order, through the injected
    IIntentDispatcher - never a plugin, workflow, or service directly
    - per factory/packages/016_AGENT_RUNTIME.md. The Runtime owns
    execution only: it never creates Plans, never validates Plans,
    never reorders PlanSteps, and never discovers capabilities - all
    of that remains Planner's, and Capability Registry's,
    responsibility.

Responsibilities:
    - start_execution / resume_execution: create (or continue) an
      Execution and dispatch its Plan's remaining PlanSteps
      sequentially through IIntentDispatcher.dispatch(), stopping
      immediately on the first failure (no retries, no rollback, no
      concurrency, per this package's explicit Constraints). Both are
      gated on the Runtime's own IService lifecycle state being
      RUNNING - see argus/runtime/interfaces.py's Architectural Note
      for why AgentRuntime, unlike the three packages immediately
      preceding it, adopts IService.
    - pause_execution / cancel_execution / get_execution /
      list_executions: ungated registry-style operations on
      individual Executions, unaffected by the Runtime's own IService
      lifecycle state - matching the precedent set by Scheduler's
      pause()/resume() (Package 008) and every metadata/reasoning
      registry's own lookup methods in this codebase.
    - Every mutation constructs a new Execution via
      dataclasses.replace and stores it under the same id - Execution
      is frozen, matching the precedent set by WorkflowEngine's
      treatment of Workflow (Package 010) and Planner's treatment of
      Plan (Package 015): mutation happens by replacement, never by
      attribute assignment.
    - Publishes ExecutionCreated once per start_execution() call,
      ExecutionStarted once execution actually begins running,
      StepStarted/StepCompleted bracketing each dispatched step, and
      exactly one of ExecutionCompleted or ExecutionFailed when a run
      reaches a terminal outcome. pause_execution()/cancel_execution()
      publish nothing - this package's Events section names exactly
      six event types to add, with no pause/resume/cancel-specific
      event among them; see factory/packages/016_AGENT_RUNTIME.md's
      Architectural Decisions for why none were invented to fill that
      gap.

Dispatcher Integration - The Synthetic-Intent Design Decision:
    IIntentDispatcher.dispatch() accepts only an Intent (resolving a
    Capability purely by the Intent's IntentType, via
    ICapabilityRegistry.find_by_intent_type()) - it has no parameter
    for a specific capability id, and this package's Constraints
    forbid modifying Dispatcher's responsibilities or contract. Since
    every PlanStep names a specific `required_capability` id rather
    than an IntentType, AgentRuntime cannot ask the Dispatcher to
    resolve that exact capability. The Runtime instead constructs a
    synthetic Intent for every dispatched step, reusing the Plan's own
    `originating_intent.name` (IntentType) - the only IntentType the
    Plan actually carries - and passes the step's `required_capability`
    id, `step_id`, `plan_id`, and `execution_id` in dispatch()'s
    `context` argument for traceability. This is a deliberate,
    documented limitation, not an oversight: in Version 1, every step
    of a given Plan resolves to whichever Capability the Dispatcher
    would select for the Plan's originating IntentType (the first
    enabled match), regardless of each step's own required_capability
    - see this module's and factory/packages/016_AGENT_RUNTIME.md's
    Known Limitations for the full rationale and what a future package
    would need to change (on the Dispatcher/Capability Registry side,
    not here) to resolve it.

Non-Responsibilities:
    - AgentRuntime never imports argus.plugins or argus.workflow, and
      never constructs, obtains, or calls an Action, a Plugin, or a
      Workflow directly - every effect of execution happens only
      through the single injected IIntentDispatcher.dispatch() call.
    - AgentRuntime never calls IPlanner.create_plan(), add_step(),
      remove_step(), reorder_steps(), or validate_plan() - its only
      touchpoint with the Planner is a read-only get_plan() call, used
      solely to confirm a Plan is currently VALIDATED and to obtain
      its canonical steps.
    - No AI, no LLM, no networking, no persistence, no retries, no
      rollback, no concurrent execution - Executions are held only in
      memory, and start_execution()/resume_execution() run entirely
      within the calling thread, returning only once every dispatched
      step has completed, one step has failed, or the Execution is no
      longer RUNNING.

Dependencies:
    argus.runtime (Execution, ExecutionStatus, IAgentRuntime, and the
    runtime exceptions), argus.dispatcher.interfaces (IIntentDispatcher),
    argus.planner.interfaces (IPlanner), argus.planner.plan (Plan,
    PlanStatus), argus.planner.exceptions (InvalidPlanError,
    PlanNotFoundError), argus.intent.intent (Intent), argus.events
    (Event, EventType, IEventBus), argus.lifecycle.lifecycle
    (LifecycleState).
"""

import dataclasses
from datetime import datetime, timezone
from typing import Dict, Sequence

from argus.dispatcher.interfaces import IIntentDispatcher
from argus.events.event import Event
from argus.events.event_types import EventType
from argus.events.interfaces import IEventBus
from argus.intent.intent import Intent
from argus.lifecycle.lifecycle import LifecycleState
from argus.planner.exceptions import InvalidPlanError, PlanNotFoundError
from argus.planner.interfaces import IPlanner
from argus.planner.plan import Plan, PlanStatus
from argus.runtime.exceptions import (
    AgentRuntimeError,
    ExecutionNotFoundError,
    InvalidExecutionError,
    InvalidExecutionStateError,
    StepExecutionError,
)
from argus.runtime.execution import Execution, ExecutionStatus
from argus.runtime.interfaces import IAgentRuntime


class AgentRuntime(IAgentRuntime):
    """
    In-memory, synchronous implementation of IAgentRuntime.

    Purpose:
        Be the only component in ArgusOS permitted to execute a Plan,
        doing so exclusively by dispatching PlanSteps through the
        injected IIntentDispatcher. See the module docstring for the
        full design rationale.

    Dependencies:
        An IEventBus, an IIntentDispatcher, and an IPlanner
        implementation, all injected by the caller (bootstrap.py).
    """

    def __init__(
        self, event_bus: IEventBus, dispatcher: IIntentDispatcher, planner: IPlanner
    ) -> None:
        self._event_bus = event_bus
        self._dispatcher = dispatcher
        self._planner = planner
        self._executions: Dict[str, Execution] = {}
        self._plans: Dict[str, Plan] = {}
        self._state: LifecycleState = LifecycleState.CREATED

    # -- IService -----------------------------------------------------

    def initialize(self) -> None:
        if self._state != LifecycleState.CREATED:
            raise AgentRuntimeError(
                f"Cannot initialize: AgentRuntime is {self._state.name}, expected CREATED."
            )
        self._state = LifecycleState.INITIALIZING

    def start(self) -> None:
        if self._state != LifecycleState.INITIALIZING:
            raise AgentRuntimeError(
                f"Cannot start: AgentRuntime is {self._state.name}, expected INITIALIZING."
            )
        self._state = LifecycleState.RUNNING

    def stop(self) -> None:
        if self._state != LifecycleState.RUNNING:
            raise AgentRuntimeError(
                f"Cannot stop: AgentRuntime is {self._state.name}, expected RUNNING."
            )
        self._state = LifecycleState.STOPPING
        self._state = LifecycleState.STOPPED

    def status(self) -> LifecycleState:
        return self._state

    # -- IAgentRuntime: start_execution / resume_execution (gated) ------

    def start_execution(self, plan: Plan) -> Execution:
        if self._state != LifecycleState.RUNNING:
            raise InvalidExecutionStateError(
                f"Cannot start_execution: AgentRuntime is {self._state.name}, expected RUNNING."
            )
        if not isinstance(plan, Plan):
            raise InvalidExecutionError(f"start_execution() requires a Plan, got {plan!r}.")

        canonical = self._require_validated_plan(plan)

        execution = Execution(plan_id=canonical.id)
        self._executions[execution.id] = execution
        self._plans[execution.id] = canonical
        self._publish(
            EventType.EXECUTION_CREATED,
            {"execution_id": execution.id, "plan_id": canonical.id},
        )

        execution = dataclasses.replace(
            execution,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        self._executions[execution.id] = execution
        self._publish(
            EventType.EXECUTION_STARTED,
            {"execution_id": execution.id, "plan_id": canonical.id},
        )

        return self._run(execution.id)

    def resume_execution(self, execution_id: str) -> Execution:
        execution = self._require_execution(execution_id)
        if self._state != LifecycleState.RUNNING:
            raise InvalidExecutionStateError(
                f"Cannot resume_execution: AgentRuntime is {self._state.name}, expected RUNNING."
            )
        if execution.status != ExecutionStatus.PAUSED:
            raise InvalidExecutionStateError(
                f"Cannot resume execution {execution_id!r}: status is "
                f"{execution.status.name}, expected PAUSED."
            )
        execution = dataclasses.replace(execution, status=ExecutionStatus.RUNNING)
        self._executions[execution_id] = execution
        return self._run(execution_id)

    # -- IAgentRuntime: registry operations (ungated) --------------------

    def pause_execution(self, execution_id: str) -> Execution:
        execution = self._require_execution(execution_id)
        if execution.status != ExecutionStatus.RUNNING:
            raise InvalidExecutionStateError(
                f"Cannot pause execution {execution_id!r}: status is "
                f"{execution.status.name}, expected RUNNING."
            )
        execution = dataclasses.replace(execution, status=ExecutionStatus.PAUSED)
        self._executions[execution_id] = execution
        return execution

    def cancel_execution(self, execution_id: str) -> Execution:
        execution = self._require_execution(execution_id)
        if execution.status in (
            ExecutionStatus.FAILED,
            ExecutionStatus.COMPLETED,
            ExecutionStatus.CANCELLED,
        ):
            raise InvalidExecutionStateError(
                f"Cannot cancel execution {execution_id!r}: status is already "
                f"terminal ({execution.status.name})."
            )
        execution = dataclasses.replace(
            execution,
            status=ExecutionStatus.CANCELLED,
            completed_at=datetime.now(timezone.utc),
        )
        self._executions[execution_id] = execution
        return execution

    def get_execution(self, execution_id: str) -> Execution:
        return self._require_execution(execution_id)

    def list_executions(self) -> Sequence[Execution]:
        return tuple(self._executions.values())

    # -- internals ------------------------------------------------------

    def _run(self, execution_id: str) -> Execution:
        """Dispatch remaining PlanSteps for the Execution registered
        under execution_id, starting at its current `current_step`,
        until every step completes, a step fails, or the Execution is
        no longer RUNNING (paused or cancelled via a reentrant call
        from within a dispatched step's own action - the only way
        either can happen mid-run, since Version 1 has no
        concurrency)."""
        plan = self._plans[execution_id]
        steps = plan.steps

        while True:
            execution = self._executions[execution_id]
            if execution.status != ExecutionStatus.RUNNING:
                return execution
            if execution.current_step >= len(steps):
                execution = dataclasses.replace(
                    execution,
                    status=ExecutionStatus.COMPLETED,
                    completed_at=datetime.now(timezone.utc),
                )
                self._executions[execution_id] = execution
                self._publish(
                    EventType.EXECUTION_COMPLETED,
                    {"execution_id": execution_id, "plan_id": plan.id},
                )
                return execution

            step = steps[execution.current_step]
            self._publish(
                EventType.STEP_STARTED,
                {
                    "execution_id": execution_id,
                    "plan_id": plan.id,
                    "step_id": step.id,
                    "step_order": step.order,
                },
            )

            synthetic_intent = Intent(
                name=plan.originating_intent.name,
                confidence=plan.originating_intent.confidence,
            )
            try:
                result = self._dispatcher.dispatch(
                    synthetic_intent,
                    context={
                        "plan_id": plan.id,
                        "execution_id": execution_id,
                        "step_id": step.id,
                        "required_capability": step.required_capability,
                    },
                )
            except Exception as error:
                wrapped = StepExecutionError(
                    f"Step {step.id!r} (order {step.order}) failed during "
                    f"execution {execution_id!r}: {error}"
                )
                failed = dataclasses.replace(
                    self._executions[execution_id],
                    status=ExecutionStatus.FAILED,
                    completed_at=datetime.now(timezone.utc),
                )
                self._executions[execution_id] = failed
                self._publish(
                    EventType.EXECUTION_FAILED,
                    {
                        "execution_id": execution_id,
                        "plan_id": plan.id,
                        "step_id": step.id,
                        "error": str(wrapped),
                    },
                )
                raise wrapped from error

            # Re-fetch rather than reuse the loop-local `execution`: a
            # reentrant pause_execution()/cancel_execution() call made
            # from within the step's own dispatched action (the only
            # way either can happen mid-run, given no concurrency) may
            # have already changed status while dispatch() was
            # running. Building the update on top of the current
            # stored state preserves that reentrant transition instead
            # of silently overwriting it.
            current = self._executions[execution_id]
            new_results = dict(current.results)
            new_results[step.id] = result
            updated = dataclasses.replace(
                current,
                current_step=execution.current_step + 1,
                results=new_results,
            )
            self._executions[execution_id] = updated
            self._publish(
                EventType.STEP_COMPLETED,
                {
                    "execution_id": execution_id,
                    "plan_id": plan.id,
                    "step_id": step.id,
                    "step_order": step.order,
                },
            )
            # Loop continues; the top-of-loop check stops immediately
            # if `updated.status` is no longer RUNNING.

    def _require_validated_plan(self, plan: Plan) -> Plan:
        try:
            canonical = self._planner.get_plan(plan.id)
        except (PlanNotFoundError, InvalidPlanError) as error:
            raise InvalidExecutionStateError(
                f"Cannot start_execution: plan {plan.id!r} is not registered "
                f"with the Planner ({error})."
            ) from error
        if canonical.status != PlanStatus.VALIDATED:
            raise InvalidExecutionStateError(
                f"Cannot start_execution: plan {plan.id!r} has status "
                f"{canonical.status.name}, expected VALIDATED."
            )
        return canonical

    def _require_execution(self, execution_id: str) -> Execution:
        if not isinstance(execution_id, str):
            raise InvalidExecutionError(
                f"execution_id must be a string, got {execution_id!r}."
            )
        try:
            return self._executions[execution_id]
        except KeyError:
            raise ExecutionNotFoundError(
                f"No execution registered with id {execution_id!r}."
            ) from None

    def _publish(self, event_type: EventType, payload: dict) -> None:
        self._event_bus.publish(
            Event(type=event_type, source="agent_runtime", payload=payload)
        )
