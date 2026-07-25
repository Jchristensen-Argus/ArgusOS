"""
Public interface contract for the ArgusOS Workflow Engine.

Purpose:
    Define the Workflow Engine's public contract independently of any
    concrete implementation, per design/specifications/INTERFACES.md's
    "no subsystem may bypass another engine's published interface" and
    factory/packages/010_WORKFLOW_ENGINE.md.

Responsibilities:
    - Declare register_workflow, execute, cancel, and get_workflow as
      the Workflow Engine's registry/execution surface, plus the
      inherited IService lifecycle (initialize/start/stop/status).

Non-Responsibilities:
    - This module implements nothing.

Dependencies:
    argus.lifecycle.interfaces (IService), argus.workflow.workflow
    (Workflow, WorkflowStep).
"""

from abc import abstractmethod
from typing import Any, Mapping, Optional, Sequence

from argus.lifecycle.interfaces import IService
from argus.workflow.workflow import Workflow, WorkflowStep


class IWorkflowEngine(IService):
    """
    Deterministic orchestration contract for ArgusOS.

    Purpose:
        Let callers register a named sequence of steps as a Workflow,
        execute it, cancel it before it runs, and inspect its current
        state - without the engine ever invoking another service
        directly (see argus/workflow/engine.py's module docstring for
        why register_workflow's steps are plain callables, not calls
        into other core services).

    Note on scope:
        The work order's Required Methods are register_workflow,
        execute, cancel, and status (the last inherited from
        IService). get_workflow is an addition beyond that literal
        list: without a way to look up a specific Workflow after
        registration or execution, the work order's own "Status
        reporting" testing requirement has nothing to inspect -
        IService.status() only reports the *engine's* lifecycle
        state, not any individual workflow's. This mirrors the
        precedent set by Scheduler (Package 008), whose interface
        also grew a get_task()/list_tasks() lookup surface beyond its
        four headline methods. Documented here and in
        IMPLEMENTATION_REPORT.md's Deviations section, not silently
        added.
    """

    @abstractmethod
    def register_workflow(
        self,
        *,
        name: str,
        steps: Sequence[WorkflowStep],
        workflow_id: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Workflow:
        """
        Register a new Workflow in the PENDING state.

        Does not execute anything. Raises InvalidWorkflowError for an
        empty name, an empty steps sequence, a non-WorkflowStep
        element, or a step whose action is not callable. Raises
        DuplicateWorkflowError if workflow_id is already registered.
        Generates a workflow_id via uuid4 if not supplied. Publishes
        no event - registration is a registry operation, not an
        execution event; only execute()/cancel() publish.
        """
        raise NotImplementedError

    @abstractmethod
    def execute(
        self, workflow_id: str, *, context: Optional[Mapping[str, Any]] = None
    ) -> Mapping[str, Any]:
        """
        Execute a registered workflow's steps sequentially, in order.

        Raises WorkflowNotFoundError if workflow_id is not registered.
        Raises WorkflowError if the workflow is not currently PENDING
        (a workflow may only be executed once), or if the engine's own
        IService state is not RUNNING (see engine.py's module
        docstring for why execute(), specifically, is gated on
        lifecycle state the same way Scheduler.tick() is).

        Publishes WorkflowStarted, then WorkflowStepStarted /
        WorkflowStepCompleted for each step in order. If a step's
        action raises, publishes WorkflowFailed, marks the workflow
        FAILED, and stops - remaining steps do not run, and the
        exception does not propagate to the caller (see
        WorkflowExecutionError's docstring). On success, publishes
        WorkflowCompleted and marks the workflow COMPLETED. Returns
        the final context mapping in either case; the workflow's own
        state (queryable via get_workflow) is the caller's signal for
        success vs. failure.
        """
        raise NotImplementedError

    @abstractmethod
    def cancel(self, workflow_id: str) -> None:
        """
        Cancel a registered workflow before it executes.

        Raises WorkflowNotFoundError if workflow_id is not registered.
        Raises WorkflowError if the workflow is not currently PENDING
        (a workflow that has already started, completed, failed, or
        been cancelled cannot be cancelled). Publishes
        WorkflowCancelled and marks the workflow CANCELLED. This
        method is not affected by the engine's own IService lifecycle
        state, matching the precedent set by Scheduler's registry
        operations (schedule/cancel/pause/resume), which are likewise
        unaffected by Scheduler's own lifecycle state - only the
        single "do real work" method (tick() for Scheduler, execute()
        here) is gated.
        """
        raise NotImplementedError

    @abstractmethod
    def get_workflow(self, workflow_id: str) -> Workflow:
        """
        Return the current Workflow snapshot for workflow_id.

        Raises WorkflowNotFoundError if workflow_id is not registered.
        Not affected by the engine's own IService lifecycle state, for
        the same reason as cancel().
        """
        raise NotImplementedError
