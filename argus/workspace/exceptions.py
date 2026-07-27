"""
Exceptions for the ArgusOS Workspace Framework package.

Purpose:
    Define the error types argus.workspace itself can raise. Per
    factory/packages/037_WORKSPACE_FRAMEWORK.md, "Workspace is a
    passive domain object only" - this package's own errors are
    therefore limited to malformed builder input, never scheduling,
    execution, or ownership-relationship failures (this package
    implements none of those).

Responsibilities:
    - WorkspaceError: the base exception for this package.
    - InvalidWorkspaceError: raised by WorkspaceBuilder's with_*()
      methods when given a malformed argument.

Non-Responsibilities:
    - This module performs no logic beyond defining exception types -
      it holds no state and makes no decisions about when to raise.

Dependencies:
    None.
"""


class WorkspaceError(Exception):
    """Base exception for the argus.workspace package."""


class InvalidWorkspaceError(WorkspaceError):
    """Raised when WorkspaceBuilder's with_name()/with_description()/
    with_status()/with_metadata() is given a malformed argument."""
