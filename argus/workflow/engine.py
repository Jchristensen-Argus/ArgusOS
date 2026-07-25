"""
WorkflowEngine: deterministic, sequential orchestration for the
ArgusOS Workflow Engine.

Purpose:
    Implement IWorkflowEngine: register named sequences of steps as
    Workflows, execute them strictly in order, and publish their
    progress on the Event Bus, per
    factory/packages/010_WORKFLOW_ENGINE.md.

Responsibilities:
    - register_workflow / cancel / get_workflow: an in-memory registry
      of Workflow objects, keyed by id. Registry operations are not
      affected by the engine's own IService lifecycle state, matching
      the precedent set by Scheduler's schedule/cancel/pause/resume
      (Package 008).
    - execute: run a PENDING workflow's steps sequentially. Each
      step's action receives the current context and returns the
      updated context for the next step. If a step raises, execution
      stops immediately, the workflow is marked FAILED, and
      WorkflowFailed is published - the exception itself never
      propagates out of execute() (see WorkflowExecutionError's
      docstring). This mirrors Scheduler's per-task failure isolation
      in tick(): one failure is contained, not silently retried
      (retries are explicitly out of scope) and not allowed to crash
      the caller.
    - initialize / start / stop / status, per the inherited IService
      contract. Unlike IntentRouter (Package 009), execute() *is*
      gated on the engine's own lifecycle state: it raises
      WorkflowError unless the engine's self-tracked state is
      RUNNING. This mirrors Scheduler.tick()'s gating exactly - a
      Workflow Engine "doing its active work" (running steps) is
      precisely the kind of behavior IService's start()/stop() docstring
      describes gating, and unlike IntentRouter's parse()/route()
      (stateless, cheap classification with no real "active work"
      phase), step execution is exactly that kind of active work.
      register_workflow/cancel/get_workflow remain ungated, matching
      Scheduler's registry-operations precedent.

Non-Responsibilities:
    - WorkflowEngine contains no service-specific knowledge: it never
      imports or references KnowledgeService, MemoryService,
      Scheduler, or IntentRouter, and step actions are opaque plain
      callables (StepAction) the engine invokes without inspecting
      what they do. A workflow that needs to touch another core
      service does so by having its step's action call that service
      directly (resolved by whoever constructs the WorkflowStep, e.g.
      via the Container) - WorkflowEngine itself never imports or
      calls another core service.
    - No threading, no background execution, no retries, no
      persistence, no AI, per the work order's explicit Non-Goals.
      execute() runs entirely within the calling thread and returns
      only once every step has run or one has failed.

Dependencies:
    argus.events (Event, EventType, IEventBus), argus.lifecycle
    (LifecycleState), argus.workflow (Workflow, WorkflowStep,
    WorkflowState, and the workflow exceptions).
"""

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional, Sequence

from argus.events.event import Event
from argus.events.event_types import EventType
from argus.events.interfaces import IEventBus
from argus.lifecycle.lifecycle import LifecycleState
from argus.workflow.exceptions import (
    DuplicateWorkflowError,
    InvalidWorkflowError,
    WorkflowError,
    WorkflowExecutionError,
    WorkflowNotFoundError,
)
from argus.workflow.interfaces import IWorkflowEngine
from argus.workflow.state import WorkflowState
from argus.workflow.workflow import Workflow, WorkflowStep


class WorkflowEngine(IWorkflowEngine):
    """
    In-memory, synchronous implementation of IWorkflowEngine.

    Purpose:
        Coordinate multi-step, deterministic sequences of work without
        the engine itself knowing anything about what any given step
        does. See the module docstring for the full design rationale.

    Responsibilities:
        - register_workflow / execute / cancel / get_workflow, per
          IWorkflowEngine.
        - Track its own IService lifecycle state, gating execute()
          on it (see the module docstring).

    Dependencies:
        An IEventBus implementation, injected by the caller
        (bootstrap.py).
    """

    def __init__(self, event_bus: IEventBus) -> None:
        self._event_bus = event_bus
        self._state: LifecycleState = LifecycleState.CREATED
        self._workflows: Dict[str, Workflow] = {}

    # -- IService -----------------------------------------------------

    def initialize(self) -> None:
        if self._state != LifecycleState.CREATED:
            raise WorkflowError(
                f"Cannot initialize: WorkflowEngine is {self._state.name}, expected CREATED."
            )
        self._state = LifecycleState.INITIALIZING

    def start(self) -> None:
        if self._state != LifecycleState.INITIALIZING:
            raise WorkflowError(
                f"Cannot start: WorkflowEngine is {self._state.name}, expected INITIALIZING."
            )
        self._state = LifecycleState.RUNNING

    def stop(self) -> None:
        if self._state != LifecycleState.RUNNING:
            raise WorkflowError(
                f"Cannot stop: WorkflowEngine is {self._state.name}, expected RUNNING."
            )
        self._state = LifecycleState.STOPPING
        self._state = LifecycleState.STOPPED

    def status(self) -> LifecycleState:
        return self._state

    # -- IWorkflowEngine: registry operations (unaffected by lifecycle state) --

    def register_workflow(
        self,
        *,
        name: str,
        steps: Sequence[WorkflowStep],
        workflow_id: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Workflow:
        if not isinstance(name, str) or not name:
            raise InvalidWorkflowError("register_workflow() requires a non-empty name.")
        if not isinstance(steps, Sequence) or len(steps) == 0:
            raise InvalidWorkflowError(
                "register_workflow() requires a non-empty sequence of steps."
            )
        for step in steps:
            if not isinstance(step, WorkflowStep):
                raise InvalidWorkflowError(
                    f"Every step must be a WorkflowStep, got {step!r}."
                )
            if not callable(step.action):
                raise InvalidWorkflowError(
                    f"Step {step.name!r}'s action must be callable, got {step.action!r}."
                )

        if workflow_id is not None and workflow_id in self._workflows:
            raise DuplicateWorkflowError(
                f"A workflow with id {workflow_id!r} is already registered."
            )

        kwargs = {"name": name, "steps": steps, "metadata": metadata or {}}
        if workflow_id is not None:
            kwargs["id"] = workflow_id
        workflow = Workflow(**kwargs)

        self._workflows[workflow.id] = workflow
        return workflow

    def cancel(self, workflow_id: str) -> None:
        workflow = self._require_workflow(workflow_id)
        if workflow.state != WorkflowState.PENDING:
            raise WorkflowError(
                f"Cannot cancel workflow {workflow_id!r}: it is "
                f"{workflow.state.name}, expected PENDING."
            )

        cancelled = replace(
            workflow,
            state=WorkflowState.CANCELLED,
            completed_at=datetime.now(timezone.utc),
        )
        self._workflows[workflow_id] = cancelled
        self._publish(
            EventType.WORKFLOW_CANCELLED,
            {"workflow_id": workflow_id, "name": workflow.name},
        )

    def get_workflow(self, workflow_id: str) -> Workflow:
        return self._require_workflow(workflow_id)

    # -- IWorkflowEngine: execution (gated on the engine's own RUNNING state) --

    def execute(
        self, workflow_id: str, *, context: Optional[Mapping[str, Any]] = None
    ) -> Mapping[str, Any]:
        if self._state != LifecycleState.RUNNING:
            raise WorkflowError(
                f"Cannot execute: WorkflowEngine is {self._state.name}, expected RUNNING."
            )

        workflow = self._require_workflow(workflow_id)
        if workflow.state != WorkflowState.PENDING:
            raise WorkflowError(
                f"Cannot execute workflow {workflow_id!r}: it is "
                f"{workflow.state.name}, expected PENDING."
            )

        now = datetime.now(timezone.utc)
        workflow = replace(workflow, state=WorkflowState.RUNNING, started_at=now)
        self._workflows[workflow_id] = workflow
        self._publish(
            EventType.WORKFLOW_STARTED,
            {"workflow_id": workflow_id, "name": workflow.name},
        )

        current_context: Dict[str, Any] = dict(context or {})

        for index, step in enumerate(workflow.steps):
            self._publish(
                EventType.WORKFLOW_STEP_STARTED,
                {"workflow_id": workflow_id, "step_name": step.name, "step_index": index},
            )
            try:
                result = step.action(current_context)
            except Exception as error:
                wrapped = WorkflowExecutionError(
                    f"Step {step.name!r} of workflow {workflow_id!r} failed: {error}"
                )
                self._finish(
                    workflow_id,
                    WorkflowState.FAILED,
                    EventType.WORKFLOW_FAILED,
                    {
                        "workflow_id": workflow_id,
                        "step_name": step.name,
                        "step_index": index,
                        "error": str(wrapped),
                    },
                )
                return current_context
            current_context = dict(result)
            self._publish(
                EventType.WORKFLOW_STEP_COMPLETED,
                {"workflow_id": workflow_id, "step_name": step.name, "step_index": index},
            )

        self._finish(
            workflow_id,
            WorkflowState.COMPLETED,
            EventType.WORKFLOW_COMPLETED,
            {"workflow_id": workflow_id, "name": workflow.name},
        )
        return current_context

    # -- internals ------------------------------------------------------

    def _require_workflow(self, workflow_id: str) -> Workflow:
        try:
            return self._workflows[workflow_id]
        except KeyError:
            raise WorkflowNotFoundError(
                f"No workflow registered with id {workflow_id!r}."
            ) from None

    def _finish(
        self,
        workflow_id: str,
        state: WorkflowState,
        event_type: EventType,
        payload: Dict[str, Any],
    ) -> None:
        workflow = self._workflows[workflow_id]
        finished = replace(
            workflow, state=state, completed_at=datetime.now(timezone.utc)
        )
        self._workflows[workflow_id] = finished
        self._publish(event_type, payload)

    def _publish(self, event_type: EventType, payload: Dict[str, Any]) -> None:
        self._event_bus.publish(
            Event(type=event_type, source="workflow_engine", payload=payload)
        )
