"""
CapabilityExecutor: in-memory deterministic dispatch for the ArgusOS
Capability Executor package.

Purpose:
    Implement ICapabilityExecutor: accept a Task, resolve a Capability
    for it against an injected CapabilityRegistry, and produce an
    immutable CapabilityExecutionResult, per
    factory/packages/034_CAPABILITY_EXECUTOR.md. "The Capability
    Executor resolves a Capability for a Task and produces an
    immutable CapabilityExecutionResult." For Package 034: no AI, no
    plugins, no external tools, no API calls, no business logic - "It
    establishes the execution contract only."

resolve() Does Exactly Two Things:
    1. Validate the Task reference (must be a Task instance) - "accept
       Task" (Responsibility 1). Raises InvalidTaskReferenceError
       otherwise.
    2. Look up `task.name` against the injected CapabilityRegistry via
       `get_by_name()` (Package 033) - "resolve Capability"
       (Responsibility 3). If a Capability is found, return a
       CapabilityExecutionResult carrying it with
       status=CapabilityExecutionStatus.COMPLETED. If
       `CapabilityNotFoundError` is raised, that is treated as a
       normal resolution outcome, not an error to propagate - return a
       CapabilityExecutionResult with capability=None and
       status=CapabilityExecutionStatus.NOT_FOUND instead. "Only
       deterministic resolution" - no other CapabilityRegistry method
       is ever called, and the found Capability is never invoked.

Why COMPLETED, Not RESOLVED, On A Successful Match:
    This package's own explicit Resolution behavior reads literally:
    "If a Capability exists whose name exactly matches the Task name,
    return: status = COMPLETED. Otherwise return: status = NOT_FOUND."
    RESOLVED might read as the more intuitive member name for "a
    Capability was found," but the work order's own text is
    unambiguous, not prose open to interpretation - implemented
    literally rather than substituted for a seemingly-more-apt
    alternative. See status.py's own module docstring for the fuller
    reasoning and for what RESOLVED remains reserved for.

Constructor Dependency - CapabilityRegistry Only, Task Is Per-Call:
    Mirrors ExecutionEngine's own "Plan Per-Call, CapabilityRegistry At
    Construction Only" shape (032, amended 033), inverted one level
    down the new dependency chain this package introduces:
    `CapabilityExecutor.__init__()` accepts `capability_registry:
    ICapabilityRegistry` - "accept CapabilityRegistry" (Responsibility
    2) - stored and genuinely called by every resolve() invocation,
    unlike ExecutionEngine's own Package 033 constructor dependency,
    which is stored but never called. `task`, like `plan` for
    ExecutionEngine, is a per-call argument to resolve(), never a
    constructor-injected collaborator.

Responsibilities:
    - resolve(): resolve one Task into one CapabilityExecutionResult,
      per the sequence above.
    - initialize / start / stop / status, per the inherited IService
      contract. resolve() is *not* gated on the executor's own
      lifecycle state being RUNNING - see interfaces.py's own
      Architectural Note for the full reasoning.

Non-Responsibilities:
    - CapabilityExecutor never implements reasoning, decision making,
      planning, tool invocation, API calls, or AI of any kind - it
      only asks the CapabilityRegistry one deterministic question per
      Task.
    - CapabilityExecutor never invokes the Capability it finds, and
      never modifies `task` or the found Capability - both are already
      immutable value objects, so this is true by construction, not by
      anything this module does to enforce it.
    - No AI, no LLM, no tool invocation, no API calls, no persistence,
      no concurrency - Version 1 processes entirely in-process, in
      memory, per this package's own explicit Constraints.

Dependencies:
    argus.task.task (Task), argus.capability.interfaces
    (ICapabilityRegistry), argus.capability.exceptions
    (CapabilityNotFoundError), argus.capability_executor.builder
    (CapabilityExecutionResultBuilder),
    argus.capability_executor.exceptions (CapabilityExecutionError,
    InvalidTaskReferenceError), argus.capability_executor.interfaces
    (ICapabilityExecutor), argus.capability_executor.result
    (CapabilityExecutionResult), argus.capability_executor.status
    (CapabilityExecutionStatus), argus.lifecycle.lifecycle
    (LifecycleState).
"""

from argus.capability.exceptions import CapabilityNotFoundError
from argus.capability.interfaces import ICapabilityRegistry
from argus.capability_executor.builder import CapabilityExecutionResultBuilder
from argus.capability_executor.exceptions import (
    CapabilityExecutionError,
    InvalidTaskReferenceError,
)
from argus.capability_executor.interfaces import ICapabilityExecutor
from argus.capability_executor.result import CapabilityExecutionResult
from argus.capability_executor.status import CapabilityExecutionStatus
from argus.lifecycle.lifecycle import LifecycleState
from argus.task.task import Task


class CapabilityExecutor(ICapabilityExecutor):
    """
    In-memory implementation of ICapabilityExecutor.

    Purpose:
        Be the sole place ArgusOS resolves a Task to a Capability by
        name - deterministic lookup only, no dispatch, no invocation,
        no business logic. See the module docstring for the full
        design rationale.

    Dependencies:
        An ICapabilityRegistry implementation, injected by the caller
        (bootstrap.py) - stored and called by every resolve()
        invocation. See the module docstring's "Constructor
        Dependency" note - `task` remains a per-call argument to
        resolve(), never a constructor-injected collaborator.
    """

    def __init__(self, capability_registry: ICapabilityRegistry) -> None:
        self._capability_registry = capability_registry
        self._state: LifecycleState = LifecycleState.CREATED

    # -- IService (see interfaces.py's Architectural Note:
    #    resolve() is never gated) --------------------------------

    def initialize(self) -> None:
        if self._state != LifecycleState.CREATED:
            raise CapabilityExecutionError(
                f"Cannot initialize: CapabilityExecutor is {self._state.name}, "
                f"expected CREATED."
            )
        self._state = LifecycleState.INITIALIZING

    def start(self) -> None:
        if self._state != LifecycleState.INITIALIZING:
            raise CapabilityExecutionError(
                f"Cannot start: CapabilityExecutor is {self._state.name}, "
                f"expected INITIALIZING."
            )
        self._state = LifecycleState.RUNNING

    def stop(self) -> None:
        if self._state != LifecycleState.RUNNING:
            raise CapabilityExecutionError(
                f"Cannot stop: CapabilityExecutor is {self._state.name}, "
                f"expected RUNNING."
            )
        self._state = LifecycleState.STOPPING
        self._state = LifecycleState.STOPPED

    def status(self) -> LifecycleState:
        return self._state

    # -- ICapabilityExecutor ---------------------------------------------

    def resolve(self, task: Task) -> CapabilityExecutionResult:
        if not isinstance(task, Task):
            raise InvalidTaskReferenceError(
                f"resolve() requires a Task, got {task!r}."
            )

        builder = CapabilityExecutionResultBuilder().with_task(task)

        try:
            capability = self._capability_registry.get_by_name(task.name)
        except CapabilityNotFoundError:
            builder.with_status(CapabilityExecutionStatus.NOT_FOUND)
            return builder.build()

        builder.with_capability(capability)
        builder.with_status(CapabilityExecutionStatus.COMPLETED)
        return builder.build()
