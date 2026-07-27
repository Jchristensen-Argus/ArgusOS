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
       ExecutionResultBuilder. For each Task, as of Package 034, first
       send it to `self._capability_executor.resolve(task)` - "Send
       Task to CapabilityExecutor. Receive CapabilityExecutionResult.
       Ignore the returned status for now" - the returned
       CapabilityExecutionResult is discarded immediately, not stored
       anywhere, not inspected, not passed to anything else - then
       call `with_completed_task(task)` exactly as before Package 034,
       mirroring `AgentService.run()`'s own identical use of
       `TraceBuilder.with_step()` once per stage (028). No tool is
       invoked, no Task is modified, and no business logic runs during
       this iteration - each Task is placed into `completed_tasks`
       exactly as received, and resolving it against the Capability
       Registry (via CapabilityExecutor) changes nothing about that
       outcome in Version 1 - "This package introduces dispatch only -
       not execution policy."
    3. Set the builder's own status to ExecutionStatus.COMPLETED -
       "Set: ExecutionStatus.COMPLETED" - unconditionally, regardless
       of how many Tasks `plan.tasks` held (including zero - an empty
       Plan vacuously completes, matching this package's own explicit
       "empty plans" Testing category, and never calls
       CapabilityExecutor.resolve() at all in that case).
    4. Call `.build()` and return the resulting ExecutionResult -
       "produce ExecutionResult" (Responsibility 4).

    `failed_tasks` is never populated in Version 1 - there is no
    Version 1 code path that ever considers a Task to have failed, per
    "Every Task is considered successfully processed." This remains
    true even when CapabilityExecutor resolves a Task to
    CapabilityExecutionStatus.NOT_FOUND - that outcome is deliberately
    ignored, per Package 034's own explicit "Ignore the returned
    status for now."

Dependency Boundary - Plan Per-Call, CapabilityExecutor At
Construction Only (Package 034 Amendment):
    Package 033's own explicit Integration instruction gave
    `ExecutionEngine.__init__()` a `capability_registry:
    ICapabilityRegistry` parameter, stored but never called - "the
    dependency exists only to establish future wiring." Package 034's
    own explicit Integration instruction is that future wiring:
    "ExecutionEngine now owns: CapabilityExecutor." Per the
    Architectural Position diagram this package's own work order
    gives - `Execution Engine -> Capability Executor -> Capability
    Registry -> Capability`, a single chain with no skip-level arrow -
    `__init__()`'s own `capability_registry` parameter is *replaced*
    by `capability_executor: ICapabilityExecutor`, not supplemented by
    it; `ExecutionEngine` no longer holds any direct reference to
    `ICapabilityRegistry` at all, since it never needed one - only
    `CapabilityExecutor` ever calls the registry directly. This is a
    breaking constructor change from Package 033's own shape,
    explicitly implied by the diagram's own single-arrow chain and the
    "ExecutionEngine now owns: CapabilityExecutor" phrasing (not
    "ExecutionEngine also owns"). See
    factory/packages/034_CAPABILITY_EXECUTOR.md's own Engineering
    Decision section for the full reasoning. Unlike Package 033's own
    constructor change, this one is NOT inert - `execute()`'s own body
    changed too (see "Construction Sequence" above), since this
    package's own dependency arrives specifically to be used, not
    merely stored for the future.

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
      only reads `plan.tasks`, sends each to CapabilityExecutor for
      deterministic resolution, and places each Task, unmodified, into
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
    argus.lifecycle.lifecycle (LifecycleState),
    argus.capability_executor.interfaces (ICapabilityExecutor) -
    Package 034, constructor-injected and called once per Task,
    replacing Package 033's own stored-but-unused
    ICapabilityRegistry.
"""

from argus.capability_executor.interfaces import ICapabilityExecutor
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
        for a validated Plan - lifecycle and dispatch only, no tools,
        no APIs, no AI, no execution policy. See the module docstring
        for the full design rationale.

    Dependencies:
        As of Package 034, an ICapabilityExecutor implementation,
        injected by the caller (bootstrap.py) - stored and called once
        per Task during execute(). See the module docstring's
        "Dependency Boundary" note - `Plan` remains a per-call argument
        to execute(), never a constructor-injected collaborator.
    """

    def __init__(self, capability_executor: ICapabilityExecutor) -> None:
        self._capability_executor = capability_executor
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
            self._capability_executor.resolve(task)
            builder.with_completed_task(task)
        builder.with_status(ExecutionStatus.COMPLETED)

        return builder.build()
