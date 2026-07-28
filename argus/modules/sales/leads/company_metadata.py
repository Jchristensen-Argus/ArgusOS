"""
MISPLACED — do not use. Corrected during the same work session that
created this file.

Company does not belong inside argus.modules.sales.leads. Per this
codebase's established convention (Task vs. TaskRelationship as
separate sibling packages, not one nested inside the other), Company
gets its own package: argus.modules.sales.companies. See
argus/modules/sales/companies/metadata.py for the real
CompanyMetadata. This file is not physically removable in the session
that created it (sandbox mount does not permit file deletion, per
design/decisions/0004_REMOVE_LEGACY_PROTOTYPE.md's same caveat); it is
left as this stub until a manual `git rm` is possible. Do not import
from this module.
"""
