"""
ArgusOS Knowledge Service package.

Purpose:
    Public entry point for the Knowledge Service subsystem. Re-exports
    the symbols other modules need (KnowledgeRecord, the
    IKnowledgeService/IKnowledgeStorage contracts, the
    KnowledgeService/JSONKnowledgeStorage implementations, and the
    knowledge exceptions) so callers can depend on `argus.knowledge`
    rather than reaching into individual submodules.

Dependencies:
    None beyond the submodules it re-exports.
"""

from argus.knowledge.exceptions import (
    DuplicateKnowledgeError,
    KnowledgeError,
    KnowledgeNotFoundError,
)
from argus.knowledge.interfaces import IKnowledgeService, IKnowledgeStorage
from argus.knowledge.knowledge_record import KnowledgeRecord
from argus.knowledge.knowledge_service import KnowledgeService
from argus.knowledge.storage import JSONKnowledgeStorage

__all__ = [
    "KnowledgeRecord",
    "IKnowledgeService",
    "IKnowledgeStorage",
    "KnowledgeService",
    "JSONKnowledgeStorage",
    "KnowledgeError",
    "KnowledgeNotFoundError",
    "DuplicateKnowledgeError",
]
