"""
Interfaces for the ArgusOS Capability Executor package.

Purpose:
    Define ICapabilityExecutionResultBuilder (the contract for a
    mutable, fluent CapabilityExecutionResult builder) and
    ICapabilityExecutor (the contract for the Capability Executor's
    own lifecycle service), per
    factory/packages/034_CAPABILITY_EXECUTOR.md.

Architectural Note - ICapabilityExecutionResultBuilder Does Not
Inherit IService:
    Exactly mirroring ICognitiveContextBuilder (022),
    IPlanningSessionBuilder (023), ITraceBuilder (028), ITaskBuilder
    (029), IRelationshipBuilder (031), IExecutionResultBuilder (032),
    and ICapabilityBuilder (033), none of which inherit IService
    either - a builder has no meaningful start/stop lifecycle of its
    own; it is a short-lived, per-use accumulator.

Architectural Note - ICapabilityExecutor DOES Inherit IService, But
resolve() Is Not Gated:
    "Register: CapabilityExecutor as a core service" is read the same
    way "Register: ExecutionEngine. One new core service" (032) and
    "Register: ResponseEngine" (027) were - "core service" is this
    codebase's own established shorthand for "adopts IService" (see
    argus/execution_engine/interfaces.py's own identical Architectural
    Note). Applying ADR-0002's criterion to resolve() independently,
    however, would NOT have suggested adoption on its own: resolve()
    is a synchronous, read-only, in-memory lookup against an
    already-injected ICapabilityRegistry - one deterministic
    "does a Capability with this name exist" question, no external
    call, no dispatch to another live service beyond that single
    already-injected collaborator, no write, and no phase distinction
    it could plausibly be gated on. This is architecturally the
    identical shape to ReasoningEngine (020), DecisionEngine (021),
    and KnowledgeGraph (018) - each also holds a genuine constructor
    dependency yet gates nothing, since none of their own methods
    perform an effectful, stateful, or external operation a
    RUNNING/not-RUNNING distinction could meaningfully police - not
    the "no constructor dependency at all" shape of ResponseEngine
    (027) or (through Package 032) ExecutionEngine. This makes
    ICapabilityExecutor the **seventh** zero-gated IService adopter in
    this codebase (after IntentRouter, KnowledgeGraph, ReasoningEngine,
    DecisionEngine, ResponseEngine, and ExecutionEngine) and the
    **sixth** case where an explicit instruction to adopt IService
    diverges from what ADR-0002's own criterion would independently
    conclude (after Packages 018, 020, 021, 027, and 032) - see
    design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md's newly
    appended Empirical Finding for this package.

Responsibilities:
    - ICapabilityExecutionResultBuilder: the contract implemented by
      CapabilityExecutionResultBuilder.
    - ICapabilityExecutor: resolve, plus the inherited IService
      contract (initialize / start / stop / status).

Non-Responsibilities:
    - This module defines no concrete behavior - see builder.py and
      executor.py.

Dependencies:
    argus.task.task (Task), argus.capability.capability (Capability),
    argus.capability_executor.result (CapabilityExecutionResult),
    argus.capability_executor.status (CapabilityExecutionStatus),
    argus.lifecycle.interfaces (IService).
"""

from abc import ABC, abstractmethod
from typing import Any

from argus.capability.capability import Capability
from argus.capability_executor.result import CapabilityExecutionResult
from argus.capability_executor.status import CapabilityExecutionStatus
from argus.lifecycle.interfaces import IService
from argus.task.task import Task


class ICapabilityExecutionResultBuilder(ABC):
    """
    Contract for a mutable, fluent CapabilityExecutionResult builder.
    See this module's docstring for why
    ICapabilityExecutionResultBuilder does not inherit IService.
    """

    @abstractmethod
    def with_task(self, task: Task) -> "ICapabilityExecutionResultBuilder":
        """Set this builder's task. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidCapabilityExecutionResultError if `task` is not a Task
        instance."""

    @abstractmethod
    def with_capability(
        self, capability: Capability
    ) -> "ICapabilityExecutionResultBuilder":
        """Set this builder's capability. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidCapabilityExecutionResultError if `capability` is not a
        Capability instance."""

    @abstractmethod
    def with_status(
        self, status: CapabilityExecutionStatus
    ) -> "ICapabilityExecutionResultBuilder":
        """Set this builder's status. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidCapabilityExecutionResultError if `status` is not a
        CapabilityExecutionStatus instance."""

    @abstractmethod
    def with_metadata(self, key: str, value: Any) -> "ICapabilityExecutionResultBuilder":
        """Set one arbitrary metadata key/value pair on the eventual
        CapabilityExecutionMetadata.extra mapping. Accumulates across
        multiple calls; the same key overwrites - last call wins.
        Raises InvalidCapabilityExecutionResultError if `key` is not a
        non-empty string."""

    @abstractmethod
    def build(self) -> CapabilityExecutionResult:
        """Construct and return a fresh, immutable
        CapabilityExecutionResult snapshot from this builder's current
        accumulated state."""


class ICapabilityExecutor(IService):
    """
    Contract for the Capability Executor's own lifecycle service. See
    this module's docstring for why ICapabilityExecutor inherits
    IService and why resolve() is never gated.
    """

    @abstractmethod
    def resolve(self, task: Task) -> CapabilityExecutionResult:
        """Accept and validate a `task` reference, and deterministically
        resolve a Capability for it against the injected
        CapabilityRegistry: if a Capability exists whose name exactly
        matches `task.name`, return a CapabilityExecutionResult with
        that Capability and status=CapabilityExecutionStatus.COMPLETED;
        otherwise return one with capability=None and
        status=CapabilityExecutionStatus.NOT_FOUND. Never invokes the
        found Capability, never modifies `task`, and performs no
        business logic of any kind - "Only deterministic resolution."
        Raises InvalidTaskReferenceError if `task` is not a Task
        instance."""
