"""
argus.task_relationship - The ArgusOS Task Relationships package.

Re-exports the public surface of the Task Relationships model: the
immutable value objects (TaskRelationship, RelationshipType,
RelationshipMetadata), the mutable builder (RelationshipBuilder) and
its interface (IRelationshipBuilder), and this package's own
exceptions. See factory/packages/031_TASK_RELATIONSHIPS.md for the
full architectural rationale. "Extend the Task domain so that Tasks
can describe immutable relationships with other Tasks. This package
does not implement scheduling, execution, or dependency resolution.
It only introduces the relationship model."
"""

from argus.task_relationship.builder import RelationshipBuilder
from argus.task_relationship.exceptions import (
    InvalidTaskRelationshipError,
    TaskRelationshipError,
)
from argus.task_relationship.interfaces import IRelationshipBuilder
from argus.task_relationship.metadata import (
    RELATIONSHIP_METADATA_VERSION,
    RelationshipMetadata,
)
from argus.task_relationship.relationship import TaskRelationship
from argus.task_relationship.relationship_type import RelationshipType

__all__ = [
    "TaskRelationship",
    "RelationshipType",
    "RelationshipMetadata",
    "RELATIONSHIP_METADATA_VERSION",
    "RelationshipBuilder",
    "IRelationshipBuilder",
    "TaskRelationshipError",
    "InvalidTaskRelationshipError",
]
