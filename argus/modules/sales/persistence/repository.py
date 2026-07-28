"""
JSON-backed storage for the Argus Sales OS Module (Sprint 1, Slice 5).

Purpose:
    Persist the Sales module's five entity collections (Company,
    Contact, Campaign, Lead, WorkItem) as one JSON array file per
    entity type, under a base directory (sales_data/ by default).
    Directly mirrors argus.memory.storage.JSONMemoryStorage and
    argus.knowledge.storage.JSONKnowledgeStorage: same atomic-write
    discipline (temp file in the same directory, then os.replace()),
    same "save() replaces the full set" contract, same
    DEFAULT_*_PATH-as-a-module-constant convention. This is that same,
    already-proven Core pattern, applied at the Module layer - not a
    new persistence mechanism, and not a new Core subsystem.

Why Five Files, Not One:
    Closer to JSONKnowledgeStorage's one-file-per-category shape than
    JSONMemoryStorage's single-file shape, because Sales's five
    entities are structurally distinct types (unlike Memory's one
    homogeneous MemoryRecord), but unlike Knowledge's categories,
    Sales's five collections are a fixed, closed set known at
    build time - so this class skips Knowledge's directory-scanning
    category discovery entirely and simply names five files.

Whole-Collection Load/Save, Not Incremental CRUD - Deliberately:
    Every save_*() call replaces that entity type's entire stored
    collection, exactly like IMemoryStorage.save()'s own contract
    ("Replace everything in storage with exactly `records`"). Sprint 1
    needs "load everything at startup, save everything after a
    mutating operation" - a full CRUD service (create/read/update/
    delete/search, the shape KnowledgeService and MemoryService
    provide) is more infrastructure than that need justifies. See
    persistence/session.py for the thin orchestration that calls these
    methods at the right moments.

No Interface (ISalesRepository) - Deliberately, For Now:
    Unlike IMemoryStorage/IKnowledgeStorage, this class has no paired
    ABC. Those interfaces exist so MemoryService/KnowledgeService can
    depend on behavior instead of a concrete JSON-file implementation.
    Nothing in Sales yet consumes SalesRepository through such an
    abstraction - session.py depends on this concrete class directly.
    Introducing an interface with a single implementation and no
    polymorphic consumer would be exactly the "unnecessary
    infrastructure" this slice was asked to avoid; add one if and when
    a second backing store or a real substitution need appears.

Responsibilities:
    - load_companies / save_companies
    - load_contacts / save_contacts
    - load_campaigns / save_campaigns
    - load_leads / save_leads
    - load_work_items / save_work_items
    Each load() returns an empty list if its file does not yet exist
    (a brand-new Sales installation has nothing to load - this is not
    an error). Each save() writes atomically.

Non-Responsibilities:
    - SalesRepository does not deduplicate, index, or validate
      entities - it stores exactly what it is given and returns
      exactly what it stored.
    - SalesRepository does not decide when to load or save, or how to
      reconcile freshly-imported entities with previously-stored ones
      - see persistence/session.py.
    - SalesRepository publishes no domain events.

Dependencies:
    argus.modules.sales.persistence.serialization (the five *_to_dict/
    *_from_dict pairs), argus.modules.sales.persistence.exceptions
    (SalesPersistenceError). Standard library only otherwise (json,
    os, tempfile, pathlib).
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence, TypeVar

from argus.modules.sales.campaigns.campaign import Campaign
from argus.modules.sales.companies.company import Company
from argus.modules.sales.contacts.contact import Contact
from argus.modules.sales.leads.lead import Lead
from argus.modules.sales.persistence import serialization
from argus.modules.sales.persistence.exceptions import SalesPersistenceError
from argus.modules.sales.work_items.work_item import WorkItem

#: Default base directory for the Sales module's persisted data,
#: relative to the process's working directory - matching
#: JSONMemoryStorage.DEFAULT_MEMORY_PATH's and
#: JSONKnowledgeStorage.DEFAULT_KNOWLEDGE_DIR's own convention.
DEFAULT_SALES_DATA_DIR = Path("sales_data")

_T = TypeVar("_T")


class SalesRepository:
    """
    JSON-file storage for the Sales module's five entity collections.
    See the module docstring for the full design rationale.
    """

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self._base_dir = Path(base_dir) if base_dir is not None else DEFAULT_SALES_DATA_DIR

    # --- Company ---------------------------------------------------

    def load_companies(self) -> List[Company]:
        return self._load("companies.json", serialization.company_from_dict)

    def save_companies(self, companies: Sequence[Company]) -> None:
        self._save("companies.json", companies, serialization.company_to_dict)

    # --- Contact -----------------------------------------------------

    def load_contacts(self) -> List[Contact]:
        return self._load("contacts.json", serialization.contact_from_dict)

    def save_contacts(self, contacts: Sequence[Contact]) -> None:
        self._save("contacts.json", contacts, serialization.contact_to_dict)

    # --- Campaign ------------------------------------------------------

    def load_campaigns(self) -> List[Campaign]:
        return self._load("campaigns.json", serialization.campaign_from_dict)

    def save_campaigns(self, campaigns: Sequence[Campaign]) -> None:
        self._save("campaigns.json", campaigns, serialization.campaign_to_dict)

    # --- Lead ----------------------------------------------------------

    def load_leads(self) -> List[Lead]:
        return self._load("leads.json", serialization.lead_from_dict)

    def save_leads(self, leads: Sequence[Lead]) -> None:
        self._save("leads.json", leads, serialization.lead_to_dict)

    # --- WorkItem --------------------------------------------------

    def load_work_items(self) -> List[WorkItem]:
        return self._load("work_items.json", serialization.work_item_from_dict)

    def save_work_items(self, work_items: Sequence[WorkItem]) -> None:
        self._save("work_items.json", work_items, serialization.work_item_to_dict)

    # --- Shared load/save machinery ---------------------------------

    def _load(self, filename: str, from_dict: Callable[[Any], _T]) -> List[_T]:
        path = self._base_dir / filename
        if not path.exists():
            return []

        try:
            with path.open("r", encoding="utf-8") as file:
                raw = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            raise SalesPersistenceError(
                f"Failed to load {path}: {error}"
            ) from error

        if not isinstance(raw, list):
            raise SalesPersistenceError(
                f"{path} must contain a JSON array, got {type(raw).__name__}."
            )

        return [from_dict(item) for item in raw]

    def _save(
        self,
        filename: str,
        records: Sequence[Any],
        to_dict: Callable[[Any], Any],
    ) -> None:
        path = self._base_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            serialized = json.dumps(
                [to_dict(record) for record in records],
                indent=2,
                sort_keys=True,
            )
        except (TypeError, ValueError) as error:
            raise SalesPersistenceError(
                f"Failed to serialize {path}: {error}"
            ) from error

        # Atomic write, identical discipline to JSONMemoryStorage.save()
        # and JSONKnowledgeStorage.save(): write to a temp file in the
        # same directory (so os.replace stays on one filesystem), then
        # replace the real file in a single filesystem operation.
        fd, tmp_path = tempfile.mkstemp(
            dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                tmp_file.write(serialized)
            os.replace(tmp_path, path)
        except OSError as error:
            raise SalesPersistenceError(
                f"Failed to save {path}: {error}"
            ) from error
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
