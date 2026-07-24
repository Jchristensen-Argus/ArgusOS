"""
JSON-backed storage for the ArgusOS Memory Service.

Purpose:
    Persist memory records as one human-readable JSON array file
    (memory/memory_store.json by default), per
    factory/packages/007_MEMORY_SERVICE.md. Unlike Package 006's
    JSONKnowledgeStorage, there is a single store, not one file per
    category: Memory has no category concept in
    design/specifications/MEMORY.md.

Responsibilities:
    - Load every stored record (expired or not - expiry is
      MemoryService's judgment, not storage's).
    - Save the full set of records atomically (write to a temp file in
      the same directory, then os.replace() into place), so a crash or
      power loss mid-write can never leave the store truncated or
      corrupted.

Non-Responsibilities:
    - JSONMemoryStorage does not index records, enforce uniqueness of
      keys, judge expiry, or publish events. That is MemoryService's
      responsibility.
    - No caching: every load() re-reads from disk.
    - Does not depend on argus.knowledge in any way, despite the
      structural similarity of the two storage implementations - the
      two packages are deliberately decoupled.

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

from argus.memory.exceptions import MemoryServiceError
from argus.memory.interfaces import IMemoryStorage
from argus.memory.memory_record import MemoryRecord

# Default location of the memory store, relative to the process's
# working directory, matching the convention established by
# Configuration.DEFAULT_CONFIG_PATH (argus/configuration.py) and
# Package 006's JSONKnowledgeStorage.DEFAULT_KNOWLEDGE_DIR.
DEFAULT_MEMORY_PATH = Path("memory/memory_store.json")


class JSONMemoryStorage(IMemoryStorage):
    """
    JSON-file implementation of IMemoryStorage.

    Purpose:
        Store every memory record as a single JSON array in one file.

    Responsibilities:
        - load / save, per IMemoryStorage.
        - Serialize/deserialize MemoryRecord <-> plain JSON-safe dicts.
        - Perform every write atomically.

    Dependencies:
        None beyond the standard library.
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = Path(path) if path is not None else DEFAULT_MEMORY_PATH

    def load(self) -> List[MemoryRecord]:
        if not self._path.exists():
            return []

        try:
            with self._path.open("r", encoding="utf-8") as file:
                raw = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            raise MemoryServiceError(
                f"Failed to load memory store from {self._path}: {error}"
            ) from error

        if not isinstance(raw, list):
            raise MemoryServiceError(
                f"Memory store file {self._path} must contain a JSON array, "
                f"got {type(raw).__name__}."
            )

        return [self._record_from_dict(item) for item in raw]

    def save(self, records: Sequence[MemoryRecord]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

        try:
            serialized = json.dumps(
                [self._record_to_dict(record) for record in records],
                indent=2,
                sort_keys=True,
            )
        except (TypeError, ValueError) as error:
            raise MemoryServiceError(
                f"Failed to serialize the memory store: {error}"
            ) from error

        # Atomic write: write to a temp file in the same directory
        # (so os.replace stays on one filesystem), then replace the
        # real file in a single filesystem operation. os.replace() is
        # atomic on both POSIX and Windows.
        fd, tmp_path = tempfile.mkstemp(
            dir=str(self._path.parent), prefix=f".{self._path.name}.", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                tmp_file.write(serialized)
            os.replace(tmp_path, self._path)
        except OSError as error:
            raise MemoryServiceError(
                f"Failed to save the memory store to {self._path}: {error}"
            ) from error
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    @staticmethod
    def _record_to_dict(record: MemoryRecord) -> Dict[str, Any]:
        return {
            "id": record.id,
            "key": record.key,
            "value": record.value,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
            "expires_at": record.expires_at.isoformat() if record.expires_at else None,
            "version": record.version,
        }

    @staticmethod
    def _record_from_dict(data: Dict[str, Any]) -> MemoryRecord:
        try:
            expires_at = data["expires_at"]
            return MemoryRecord(
                id=data["id"],
                key=data["key"],
                value=data["value"],
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
                expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
                version=data["version"],
            )
        except (KeyError, TypeError, ValueError) as error:
            raise MemoryServiceError(f"Malformed memory record {data!r}: {error}") from error
