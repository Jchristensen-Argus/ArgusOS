"""
argus.policy - The ArgusOS Policy Framework package.

Re-exports the public surface of the Policy Framework: the immutable
value objects (Policy, PolicyStatus, PolicyScope, PolicyMetadata), the
mutable builder (PolicyBuilder) and its interface (IPolicyBuilder), and
this package's own exceptions. See
factory/packages/040_POLICY_FRAMEWORK.md for the full architectural
rationale. "A Policy defines constraints, preferences, or governance
that influence future execution." Policies answer one question: "Under
what rules should Argus operate?" This package introduces the Policy
model only - no enforcement, no execution, no Policy Engine, no AI
integration, no bootstrap changes.
"""

from argus.policy.builder import PolicyBuilder
from argus.policy.exceptions import InvalidPolicyError, PolicyError
from argus.policy.interfaces import IPolicyBuilder
from argus.policy.metadata import POLICY_METADATA_VERSION, PolicyMetadata
from argus.policy.policy import Policy
from argus.policy.scope import PolicyScope
from argus.policy.status import PolicyStatus

__all__ = [
    "Policy",
    "PolicyStatus",
    "PolicyScope",
    "PolicyMetadata",
    "POLICY_METADATA_VERSION",
    "PolicyBuilder",
    "IPolicyBuilder",
    "PolicyError",
    "InvalidPolicyError",
]
