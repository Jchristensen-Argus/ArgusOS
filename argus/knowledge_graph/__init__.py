"""
Public re-exports for the ArgusOS Knowledge Graph package.

Purpose:
    Give callers a single, stable import surface
    (`from argus.knowledge_graph import ...`) instead of reaching into
    individual submodules, matching the convention established by
    argus/connectors/__init__.py, argus/runtime/__init__.py,
    argus/planner/__init__.py, argus/plugins/__init__.py, and
    argus/capability/__init__.py.

Dependencies:
    argus.knowledge_graph.entity, argus.knowledge_graph.exceptions,
    argus.knowledge_graph.graph, argus.knowledge_graph.interfaces,
    argus.knowledge_graph.relationship.
"""

from argus.knowledge_graph.entity import Entity
from argus.knowledge_graph.exceptions import (
    DuplicateEntityError,
    DuplicateRelationshipError,
    EntityNotFoundError,
    InvalidEntityError,
    InvalidRelationshipError,
    KnowledgeGraphError,
    RelationshipNotFoundError,
)
from argus.knowledge_graph.graph import KnowledgeGraph
from argus.knowledge_graph.interfaces import IKnowledgeGraph
from argus.knowledge_graph.relationship import Relationship

__all__ = [
    "Entity",
    "Relationship",
    "IKnowledgeGraph",
    "KnowledgeGraph",
    "KnowledgeGraphError",
    "InvalidEntityError",
    "DuplicateEntityError",
    "EntityNotFoundError",
    "InvalidRelationshipError",
    "DuplicateRelationshipError",
    "RelationshipNotFoundError",
]
