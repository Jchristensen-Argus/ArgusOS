"""
Public interface contract for the ArgusOS Agent Runtime.

Purpose:
    Define IAgentRuntime, the contract other modules depend on, per
    factory/packages/016_AGENT_RUNTIME.md.

Architectural Note - Why IAgentRuntime DOES Inherit IService:
    Unlike Capability Registry (013), Plugin Manager (014), and
    Planner (015) - three consecutive deliberate non-adopters - the
    Agent Runtime is squarely an execution engine, not a metadata or
    reasoning store: "The Runtime owns execution only." Per ADR-0002's
    proposed criterion ("adopt IService only when start()/stop() would
    do real, distinct work"), start_execution() and resume_execution()
    - the two methods that actually dispatch PlanSteps through the
    Dispatcher - are gated on the Runtime's own lifecycle state being
    RUNNING, exactly mirroring WorkflowEngine.execute()'s (Package
    010), ConversationManager.receive()'s (Package 011), and
    IntentDispatcher.dispatch()'s (Package 012) identical gate on
    their own single "do real work" method. pause_execution(),
    cancel_execution(), get_execution(), and list_executions() remain
    ungated registry-style operations on individual Executions,
    matching the precedent set by Scheduler's pause()/resume()
    (Package 008) and CapabilityRegistry's/PluginManager's/Planner's
    own registry operations - none of which are affected by the
    owning service's IService lifecycle. AgentRuntime is registered
    with the Lifecycle Manager as LifecycleState.REGISTERED only
    (never started) by bootstrap.py, exactly like every other
    IService adopter in this codebase - see
    design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md's newly
    appended Empirical Finding for this package, which records
    AgentRuntime as the sixth IService adopter and the fifth
    genuinely-gated one.

Responsibilities:
    - IAgentRuntime: start_execution / pause_execution /
      resume_execution / cancel_execution / get_execution /
      list_executions, plus the inherited IService contract
      (initialize / start / stop / status).

Non-Responsibilities:
    - This module implements no behavior; see
      argus.runtime.runtime.AgentRuntime.
    - IAgentRuntime does not create Plans, validate Plans, reorder
      PlanSteps, discover capabilities, or call plugins/workflows/
      services directly - see this package's Architectural Guidance
      and argus.planner.planner.Planner / argus.dispatcher.dispatcher.
      IntentDispatcher / argus.plugins.manager.PluginManager for those
      responsibilities.

Dependencies:
    argus.runtime.execution (Execution), argus.planner.plan (Plan).
"""

from abc import abstractmethod
from typing import Sequence

from argus.lifecycle.interfaces import IService
from argus.planner.plan import Plan
from argus.runtime.execution import Execution


class IAgentRuntime(IService):
    """
    Execution-only contract for running a validated Plan through the
    existing Dispatcher.

    Purpose:
        Let callers start, pause, resume, cancel, and inspect
        Executions of already-validated Plans, without the Runtime
        itself creating Plans, validating them, discovering
        capabilities, or invoking a plugin, workflow, or service
        directly - see this module's Architectural Note for why this
        interface inherits IService, unlike the three packages
        immediately preceding it.
    """

    @abstractmethod
    def start_execution(self, plan: Plan) -> Execution:
        """Create a new Execution for `plan` and run it: dispatch
        every PlanStep in `plan.steps`, in order, through the injected
        IIntentDispatcher, stopping immediately if any step fails.
        Raises InvalidExecutionError if plan is not a Plan instance.
        Raises InvalidExecutionStateError if the Runtime's own
        IService state is not RUNNING, or if the injected IPlanner's
        own canonical record of this plan (by plan.id) does not have
        PlanStatus.VALIDATED. Raises StepExecutionError (and persists
        the Execution as FAILED) if a step's dispatch() call raises."""

    @abstractmethod
    def pause_execution(self, execution_id: str) -> Execution:
        """Set the Execution registered under execution_id to
        ExecutionStatus.PAUSED, and return it. Raises
        InvalidExecutionError if execution_id is not a string. Raises
        ExecutionNotFoundError if execution_id has no registered
        Execution. Raises InvalidExecutionStateError if that
        Execution's status is not RUNNING. Not gated on the Runtime's
        own IService state - a pure registry operation."""

    @abstractmethod
    def resume_execution(self, execution_id: str) -> Execution:
        """Resume the Execution registered under execution_id from
        its current_step, dispatching any remaining PlanSteps through
        the injected IIntentDispatcher exactly as start_execution()
        does. Raises InvalidExecutionError if execution_id is not a
        string. Raises ExecutionNotFoundError if execution_id has no
        registered Execution. Raises InvalidExecutionStateError if
        that Execution's status is not PAUSED, or if the Runtime's own
        IService state is not RUNNING. Raises StepExecutionError (and
        persists the Execution as FAILED) if a step's dispatch() call
        raises."""

    @abstractmethod
    def cancel_execution(self, execution_id: str) -> Execution:
        """Set the Execution registered under execution_id to
        ExecutionStatus.CANCELLED, and return it. Raises
        InvalidExecutionError if execution_id is not a string. Raises
        ExecutionNotFoundError if execution_id has no registered
        Execution. Raises InvalidExecutionStateError if that
        Execution's status is already terminal (FAILED, COMPLETED, or
        CANCELLED). Not gated on the Runtime's own IService state - a
        pure registry operation."""

    @abstractmethod
    def get_execution(self, execution_id: str) -> Execution:
        """Return the Execution registered under execution_id. Raises
        InvalidExecutionError if execution_id is not a string. Raises
        ExecutionNotFoundError if execution_id has no registered
        Execution."""

    @abstractmethod
    def list_executions(self) -> Sequence[Execution]:
        """Return every registered Execution, in creation order."""
