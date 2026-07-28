"""
The Company value object for the Argus Sales OS Companies package.

Purpose:
    Represent a single company (account) a Lead or Contact belongs to,
    as an immutable value object, per
    ARGUS_SALES_OS_V1_ARCHITECTURE.md's canonical data models. Mirrors
    argus.modules.sales.leads.lead.Lead's own shape exactly: a frozen
    dataclass, every field defaulted so Company() is always valid, no
    validation of its own beyond typing - see builder.py for where
    malformed input is rejected.

Why Company Is Its Own Package, Not Nested Inside leads/:
    Per this codebase's established convention - Task (029) and
    TaskRelationship (031) are separate sibling packages, not one
    nested inside the other, even though a TaskRelationship is
    meaningless without the Tasks it connects. A Lead references
    `company_id` (a plain string), never a live Company instance or
    an import of this module - the same "pure, dependency-free leaf"
    relationship Task has with TaskRelationship, applied in reverse
    (the referenced entity, not the referencing one, is the leaf
    here).

No Validation Here - See builder.py:
    Like every other value object in this codebase, Company performs
    no validation of its own fields in `__post_init__` beyond the
    standard `metadata` typing.

Responsibilities:
    - Company: hold identity (`company_id`), descriptive fields
      (`name`, `industry`, `website`, `territory`), free-text `notes`,
      and descriptive CompanyMetadata, as an immutable value object.

Non-Responsibilities:
    - Company performs no reasoning, scheduling, or synchronization of
      any kind.
    - Company does not reference any Lead or Contact - referencing
      runs the other direction (Lead.company_id, Contact.company_id).

Dependencies:
    argus.modules.sales.companies.metadata (CompanyMetadata).
"""

import uuid
from dataclasses import dataclass, field

from argus.modules.sales.companies.metadata import CompanyMetadata


@dataclass(frozen=True)
class Company:
    """
    An immutable record of one company (account). See the module
    docstring for the full field semantics.

    Fields:
        company_id: Unique identifier for this Company. Defaults to a
            fresh uuid4 string.
        name: The company's name. Defaults to an empty string.
        industry: A free-text industry label. Defaults to an empty
            string.
        website: The company's website. Defaults to an empty string.
        territory: A free-text territory label, matching Lead's own
            `territory` field for consistent filtering/routing.
            Defaults to an empty string.
        notes: Free-text notes. Defaults to an empty string.
        metadata: Descriptive bookkeeping about this Company. Defaults
            to a fresh CompanyMetadata.
    """

    company_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    industry: str = ""
    website: str = ""
    territory: str = ""
    notes: str = ""
    metadata: CompanyMetadata = field(default_factory=CompanyMetadata)
