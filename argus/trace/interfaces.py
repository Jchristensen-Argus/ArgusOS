"""
Interfaces for the ArgusOS Execution Trace package.

Purpose:
    Define ITraceBuilder, the contract for a mutable, fluent
    ExecutionTrace builder - per factory/packages/028_EXECUTION_TRACE.md.
    "TraceBuilder is not a service." ITraceBuilder therefore does not
    inherit IService, exactly mirroring ICognitiveContextBuilder (022)
    and IPlanningSessionBuilder (023), neither of which inherit
    IService either - a builder has no meaningful start/stop lifecycle
    of its own; it is a short-lived, per-request accumulator.

Responsibilities:
    - ITraceBuilder: the contract implemented by TraceBuilder.

Non-Responsibilities:
    - This module defines no concrete behavior - see builder.py.

Dependencies:
    argus.trace.trace (ExecutionTrace).
"""

from abc import ABC, abstractmethod
from typing import Any, Mapping, Optional

from argus.trace.trace import ExecutionTrace


class ITraceBuilder(ABC):
    """
    Contract for a mutable, fluent ExecutionTrace builder. See this
    module's docstring for why ITraceBuilder does not inherit
    IService.
    """

    @abstractmethod
    def with_step(
        self,
        component: str,
        action: str,
        *,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> "ITraceBuilder":
        """Construct and append one immutable TraceStep, in call
        order. Accumulates across multiple calls. Raises
        InvalidTraceStepError if `component` or `action` is not a
        non-empty string."""

    @abstractmethod
    def with_metadata(self, key: str, value: Any) -> "ITraceBuilder":
        """Set one arbitrary metadata key/value pair on the eventual
        TraceMetadata.extra mapping. Accumulates across multiple
        calls; the same key overwrites - last call wins. Raises
        InvalidTraceStepError if `key` is not a non-empty string."""

    @abstractmethod
    def build(self) -> ExecutionTrace:
        """Construct and return a fresh, immutable ExecutionTrace
        snapshot from this builder's current accumulated state."""
