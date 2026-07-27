"""
Exceptions for the ArgusOS Project Framework package.

Purpose:
    Define the error types argus.project itself can raise. Per
    factory/packages/036_PROJECT_FRAMEWORK.md, "Project is a passive
    domain object only" - this package's own errors are therefore
    limited to malformed builder input, never scheduling, execution,
    or ownership-relationship failures (this package implements
    none of those).

Responsibilities:
    - ProjectError: the base exception for this package.
    - InvalidProjectError: raised by ProjectBuilder's with_*() methods
      when given a malformed argument.

Non-Responsibilities:
    - This module performs no logic beyond defining exception types -
      it holds no state and makes no decisions about when to raise.

Dependencies:
    None.
"""


class ProjectError(Exception):
    """Base exception for the argus.project package."""


class InvalidProjectError(ProjectError):
    """Raised when ProjectBuilder's with_name()/with_description()/
    with_status()/with_metadata() is given a malformed argument."""
