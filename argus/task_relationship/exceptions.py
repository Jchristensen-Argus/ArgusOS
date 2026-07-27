"""
Exceptions for the ArgusOS Task Relationships package.

Purpose:
    Define the error types argus.task_relationship itself can raise.
    Per factory/packages/031_TASK_RELATIONSHIPS.md, "Relationships
    describe work - they do not coordinate it" - this package's own
    errors are therefore limited to malformed builder input, never
    scheduling, dependency-resolution, or execution failures (this
    package implements none of those).

Responsibilities:
    - TaskRelationshipError: the base exception for this package.
    - InvalidTaskRelationshipError: raised by RelationshipBuilder's
      with_*() methods when given a malformed argument, and by
      TaskBuilder's with_relationship()/with_relationships() when
      given a malformed or duplicate TaskRelationship.

Non-Responsibilities:
    - This module performs no logic beyond defining exception types -
      it holds no state and makes no decisions about when to raise.

Dependencies:
    None.
"""


class TaskRelationshipError(Exception):
    """Base exception for the argus.task_relationship package."""


class InvalidTaskRelationshipError(TaskRelationshipError):
    """Raised when RelationshipBuilder's with_source_task()/
    with_target_task()/with_type()/with_metadata() is given a
    malformed argument, or when a TaskRelationship with a duplicate
    relationship_id is added to a Task via TaskBuilder."""
