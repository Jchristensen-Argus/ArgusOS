"""
JSON-backed storage for the ArgusOS Knowledge Service.

Purpose:
    Persist knowledge records as one human-readable JSON array per
    category, under the repository's knowledge/ directory, per
    factory/packages/006_KNOWLEDGE_SERVICE.md.

Responsibilities:
    - Discover categories by scanning for `knowledge/*.json` files.
    - Load a category's records from its JSON file.
    - Save a category's records atomically (write to a temp file in
      the same directory, then os.replace() into place), so a crash or
      power loss mid-write can never leave a category file truncated
      or corrupted.

Non-Responsibilities:
    - JSONKnowledgeStorage does not index records, enforce uniqueness
      of keys, or publish events. That is KnowledgeService's
      responsibility.
    - No caching: every load() re-reads from disk.

Dependencies:
    None (standard library only: json, os, tempfile, pathlib,
    datetime).
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from argus.knowledge.exceptions import KnowledgeError
from argus.knowledge.interfaces import IKnowledgeStorage
from argus.knowledge.knowledge_record import KnowledgeRecord

# Default location of the knowledge/ directory, relative to the
# process's working directory, matching the convention established by
# Configuration.DEFAULT_CONFIG_PATH (argus/configuration.py).
DEFAULT_KNOWLEDGE_DIR = Path("knowledge")


class JSONKnowledgeStorage(IKnowledgeStorage):
    """
    JSON-file implementation of IKnowledgeStorage.

    Purpose:
        Store each knowledge category as its own `<category>.json`
        file containing a JSON array of records, under a base
        directory (knowledge/ by default).

    Responsibilities:
        - list_categories / load / save, per IKnowledgeStorage.
        - Serialize/deserialize KnowledgeRecord <-> plain JSON-safe
          dicts.
        - Perform every write atomically.

    Dependencies:
        None beyond the standard library.
    """

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self._base_dir = Path(base_dir) if base_dir is not None else DEFAULT_KNOWLEDGE_DIR

    def list_categories(self) -> List[str]:
        if not self._base_dir.exists():
            return []
        return sorted(path.stem for path in self._base_dir.glob("*.json"))

    def load(self, category: str) -> List[KnowledgeRecord]:
        path = self._path_for(category)
        if not path.exists():
            return []

        try:
            with path.open("r", encoding="utf-8") as file:
                raw = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            raise KnowledgeError(
                f"Failed to load knowledge category {category!r} from {path}: {error}"
            ) from error

        if not isinstance(raw, list):
            raise KnowledgeError(
                f"Knowledge category file {path} must contain a JSON array, got {type(raw).__name__}."
            )

        return [self._record_from_dict(item) for item in raw]

    def save(self, category: str, records: Sequence[KnowledgeRecord]) -> None:
        path = self._path_for(category)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            serialized = json.dumps(
                [self._record_to_dict(record) for record in records],
                indent=2,
                sort_keys=True,
            )
        except (TypeError, ValueError) as error:
            raise KnowledgeError(
                f"Failed to serialize knowledge category {category!r}: {error}"
            ) from error

        # Atomic write: write to a temp file in the same directory
        # (so os.replace stays on one filesystem), then replace the
        # real file in a single filesystem operation. os.replace() is
        # atomic on both POSIX and Windows.
        fd, tmp_path = tempfile.mkstemp(
            dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                tmp_file.write(serialized)
            os.replace(tmp_path, path)
        except OSError as error:
            raise KnowledgeError(
                f"Failed to save knowledge category {category!r} to {path}: {error}"
            ) from error
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def _path_for(self, category: str) -> Path:
        return self._base_dir / f"{category}.json"

    @staticmethod
    def _record_to_dict(record: KnowledgeRecord) -> Dict[str, Any]:
        return {
            "id": record.id,
            "category": record.category,
            "key": record.key,
            "value": record.value,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
            "version": record.version,
        }

    @staticmethod
    def _record_from_dict(data: Dict[str, Any]) -> KnowledgeRecord:
        try:
            return KnowledgeRecord(
                id=data["id"],
                category=data["category"],
                key=data["key"],
                value=data["value"],
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
                version=data["version"],
            )
        except (KeyError, TypeError, ValueError) as error:
            raise KnowledgeError(f"Malformed knowledge record {data!r}: {error}") from error
