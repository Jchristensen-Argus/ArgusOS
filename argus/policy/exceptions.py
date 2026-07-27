"""
Exceptions for the ArgusOS Policy Framework package.

Purpose:
    Define the error types argus.policy itself can raise. Per
    factory/packages/040_POLICY_FRAMEWORK.md, "Policy is a passive
    domain object only" - this package's own errors are therefore
    limited to malformed builder input, never enforcement, evaluation,
    or governance-relationship failures (this package implements none
    of those).

Responsibilities:
    - PolicyError: the base exception for this package.
    - InvalidPolicyError: raised by PolicyBuilder's with_*() methods
      when given a malformed argument.

Non-Responsibilities:
    - This module performs no logic beyond defining exception types -
      it holds no state and makes no decisions about when to raise.

Dependencies:
    None.
"""


class PolicyError(Exception):
    """Base exception for the argus.policy package."""


class InvalidPolicyError(PolicyError):
    """Raised when PolicyBuilder's with_name()/with_description()/
    with_status()/with_scope()/with_metadata() is given a malformed
    argument."""
