"""
ExecutionEngine: in-memory lifecycle establishment for the ArgusOS
Execution Engine package.

Purpose:
    Implement IExecutionEngine: accept a validated Plan and produce an
    immutable ExecutionResult, per
    factory/packages/032_EXECUTION_ENGINE.md. "The Execution Engine
    accepts a Plan and produces an immutable ExecutionResult. It does
    not execute tools. It does not call APIs. It does not invoke AI.
    It simply establishes the execution lifecycle."

Construction Sequence - execute() Does Exactly Four Things:
    1. Validate the Plan reference (must be a Plan instance) -
       "validate Plan" (Responsibility 2). Raises
       InvalidPlanReferenceError otherwise.
    2. Iterate through `plan.tasks`, in order - "iterate through
       ordered Tasks" (Responsibility 3) - using a fresh
       ExecutionResultBuilder, calling `with_completed_task(task)`
       once per Task, mirroring `AgentService.run()`'s own identical
       use of `TraceBuilder.with_step()` once per stage (028). "For
       Package 032: Every Task is considered successfully processed...
       Simply place every Task into: completed_tasks." No tool is
       invoked, no Task is modified, and no business logic runs during
       this iteration - each Task is placed into `completed_tasks`
       exactly as received.
    3. Set the builder's own status to ExecutionStatus.COMPLETED -
       "Set: ExecutionStatus.COMPLETED" - unconditionally, regardless
       of how many Tasks `plan.tasks` held (including zero - an empty
       Plan vacuously completes, matching this package's own explicit
       "empty plans" Testing category).
    4. Call `.build()` and return the resulting ExecutionResult -
       "produce ExecutionResult" (Responsibility 4).

    `failed_tasks` is never populated in Version 1 - there is no
    Version 1 code path that ever considers a Task to have failed, per
    "Every Task is considered successfully processed."

Dependency Boundary - Plan Only, Nothing Else, Not Even At
Construction:
    Mirrors ResponseEngine's (027) own "Plan only" dependency shape
    exactly: `Plan` is not a live service to inject at construction
    time, but a per-call argument to `execute()` itself.
    `ExecutionEngine.__init__()` therefore takes no constructor
    dependency at all - no `IEventBus`, no `IPlanner`, no
    `ICognitivePipeline`, no `IResponseEngine`, nothing - the second
    core service in this codebase (after ResponseEngine, 027) for
    which that is true. See interfaces.py's own Architectural Note for
    the full ADR-0002 reasoning.

Responsibilities:
    - execute(): transform one Plan into one ExecutionResult, per the
      sequence above.
    - initialize / start / stop / status, per the inherited IService
      contract. execute() is *not* gated on the engine's own
      lifecycle state being RUNNING - see interfaces.py's own
      Architectural Note for the full reasoning.

Non-Responsibilities:
    - ExecutionEngine never implements reasoning, decision making,
      planning, tool invocation, API calls, or AI of any kind - it
      only reads `plan.tasks` and places each Task, unmodified, into
      the ExecutionResult it builds.
    - ExecutionEngine never modifies any object it is given or
      constructs - `Plan` and every `Task` it holds are already
      immutable value objects, so this is true by construction, not
      by anything this module does to enforce it.
    - No AI, no LLM, no tool invocation, no API calls, no persistence,
      no concurrency - Version 1 processes entirely in-process, in
      memory, per this package's own explicit Constraints.

Dependencies:
    argus.planner.plan (Plan), argus.execution_engine.builder
    (ExecutionResultBuilder), argus.execution_engine.exceptions
    (ExecutionError, InvalidPlanReferenceError),
    argus.execution_engine.interfaces (IExecutionEngine),
    argus.execution_engine.result (ExecutionResult),
    argus.execution_engine.status (ExecutionStatus),
    argus.lifecycle.lifecycle (LifecycleState).
"""

from argus.execution_engine.builder import ExecutionResultBuilder
from argus.execution_engine.exceptions import ExecutionError, InvalidPlanReferenceError
from argus.execution_engine.interfaces import IExecutionEngine
from argus.execution_engine.result import ExecutionResult
from argus.execution_engine.status import ExecutionStatus
from argus.lifecycle.lifecycle import LifecycleState
from argus.planner.plan import Plan


class ExecutionEngine(IExecutionEngine):
    """
    In-memory implementation of IExecutionEngine.

    Purpose:
        Be the sole place ArgusOS establishes the execution lifecycle
        for a validated Plan - lifecycle only, no tools, no APIs, no
        AI. See the module docstring for the full design rationale.

    Dependencies:
        None injected at construction. See the module docstring's
        "Dependency Boundary" note - `Plan` is a per-call argument to
        execute(), not a constructor-injected collaborator.
    """

    def __init__(self) -> None:
        self._state: LifecycleState = LifecycleState.CREATED

    # -- IService (see interfaces.py's Architectural Note:
    #    execute() is never gated) -----------------------------------

    def initialize(self) -> None:
        if self._state != LifecycleState.CREATED:
            raise ExecutionError(
                f"Cannot initialize: ExecutionEngine is {self._state.name}, "
                f"expected CREATED."
            )
        self._state = LifecycleState.INITIALIZING

    def start(self) -> None:
        if self._state != LifecycleState.INITIALIZING:
            raise ExecutionError(
                f"Cannot start: ExecutionEngine is {self._state.name}, "
                f"expected INITIALIZING."
            )
        self._state = LifecycleState.RUNNING

    def stop(self) -> None:
        if self._state != LifecycleState.RUNNING:
            raise ExecutionError(
                f"Cannot stop: ExecutionEngine is {self._state.name}, expected RUNNING."
            )
        self._state = LifecycleState.STOPPING
        self._state = LifecycleState.STOPPED

    def status(self) -> LifecycleState:
        return self._state

    # -- IExecutionEngine -------------------------------------------------

    def execute(self, plan: Plan) -> ExecutionResult:
        if not isinstance(plan, Plan):
            raise InvalidPlanReferenceError(
                f"execute() requires a Plan, got {plan!r}."
            )

        builder = ExecutionResultBuilder().with_plan(plan)
        for task in plan.tasks:
            builder.with_completed_task(task)
        builder.with_status(ExecutionStatus.COMPLETED)

        return builder.build()
