"""
Exceptions for the ArgusOS Task Model package.

Purpose:
    Define the error types argus.task itself can raise. Per
    factory/packages/029_TASK_MODEL.md, "The Task is a description of
    work, not work itself" - this package's own errors are therefore
    limited to malformed builder input, never execution or scheduling
    failures (this package implements neither).

Responsibilities:
    - TaskError: the base exception for this package.
    - InvalidTaskError: raised by TaskBuilder's with_*() methods when
      given a malformed argument.

Non-Responsibilities:
    - This module performs no logic beyond defining exception types -
      it holds no state and makes no decisions about when to raise.

Dependencies:
    None.
"""


class TaskError(Exception):
    """Base exception for the argus.task package."""


class InvalidTaskError(TaskError):
    """Raised when TaskBuilder's with_name()/with_description()/
    with_status()/with_metadata() is given a malformed argument."""
