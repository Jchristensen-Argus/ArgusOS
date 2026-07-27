"""
Interfaces for the ArgusOS Policy Framework package.

Purpose:
    Define IPolicyBuilder, the contract for a mutable, fluent Policy
    builder - per factory/packages/040_POLICY_FRAMEWORK.md. This
    package introduces no new service; IPolicyBuilder therefore does
    not inherit IService, exactly mirroring IProjectBuilder (036),
    IWorkspaceBuilder (037), IGoalBuilder (038), and
    IDecisionRecordBuilder (039), none of which inherit IService
    either - a builder has no meaningful start/stop lifecycle of its
    own; it is a short-lived, per-use accumulator.

Responsibilities:
    - IPolicyBuilder: the contract implemented by PolicyBuilder.

Non-Responsibilities:
    - This module defines no concrete behavior - see builder.py.

Dependencies:
    argus.policy.policy (Policy), argus.policy.status (PolicyStatus),
    argus.policy.scope (PolicyScope).
"""

from abc import ABC, abstractmethod
from typing import Any

from argus.policy.policy import Policy
from argus.policy.scope import PolicyScope
from argus.policy.status import PolicyStatus


class IPolicyBuilder(ABC):
    """
    Contract for a mutable, fluent Policy builder. See this module's
    docstring for why IPolicyBuilder does not inherit IService.
    """

    @abstractmethod
    def with_name(self, name: str) -> "IPolicyBuilder":
        """Set this builder's name. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidPolicyError if `name` is not a non-empty string."""

    @abstractmethod
    def with_description(self, description: str) -> "IPolicyBuilder":
        """Set this builder's description. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidPolicyError if `description` is not a string."""

    @abstractmethod
    def with_status(self, status: PolicyStatus) -> "IPolicyBuilder":
        """Set this builder's status. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidPolicyError if `status` is not a PolicyStatus
        instance."""

    @abstractmethod
    def with_scope(self, scope: PolicyScope) -> "IPolicyBuilder":
        """Set this builder's scope. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidPolicyError if `scope` is not a PolicyScope
        instance."""

    @abstractmethod
    def with_metadata(self, key: str, value: Any) -> "IPolicyBuilder":
        """Set one arbitrary metadata key/value pair on the eventual
        PolicyMetadata.extra mapping. Accumulates across multiple
        calls; the same key overwrites - last call wins. Raises
        InvalidPolicyError if `key` is not a non-empty string."""

    @abstractmethod
    def build(self) -> Policy:
        """Construct and return a fresh, immutable Policy snapshot
        from this builder's current accumulated state."""
