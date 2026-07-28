"""
Exceptions for the Argus Sales OS Lead Workspace package.

Purpose:
    Define the error types argus.modules.sales.leads itself can
    raise. Mirrors argus.task.exceptions's shape: a base error plus
    one "invalid builder input" error, since this package - like
    argus.task - implements no execution, sync, or scheduling logic
    of its own in Sprint 1.

Responsibilities:
    - LeadError: the base exception for this package.
    - InvalidLeadError: raised by LeadBuilder's with_*() methods when
      given a malformed argument.

Non-Responsibilities:
    - This module performs no logic beyond defining exception types -
      it holds no state and makes no decisions about when to raise.

Dependencies:
    None.
"""


class LeadError(Exception):
    """Base exception for the argus.modules.sales.leads package."""


class InvalidLeadError(LeadError):
    """Raised when LeadBuilder's with_*() methods are given a
    malformed argument."""
