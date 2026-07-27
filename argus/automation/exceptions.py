"""
Exceptions for the ArgusOS Automation Framework package.

Purpose:
    Define the error types argus.automation itself can raise. Per
    factory/packages/041_AUTOMATION_FRAMEWORK.md, "Automation is a
    passive domain object only" - this package's own errors are
    therefore limited to malformed builder input, never scheduling,
    execution, or relationship failures (this package implements none
    of those).

Responsibilities:
    - AutomationError: the base exception for this package.
    - InvalidAutomationError: raised by AutomationBuilder's with_*()
      methods when given a malformed argument.

Non-Responsibilities:
    - This module performs no logic beyond defining exception types -
      it holds no state and makes no decisions about when to raise.

Dependencies:
    None.
"""


class AutomationError(Exception):
    """Base exception for the argus.automation package."""


class InvalidAutomationError(AutomationError):
    """Raised when AutomationBuilder's with_name()/with_description()/
    with_status()/with_trigger()/with_metadata() is given a malformed
    argument."""
