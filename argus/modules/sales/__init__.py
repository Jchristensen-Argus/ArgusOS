"""
argus.modules.sales - The Argus Sales OS Module.

Design rationale: see ARGUS_SALES_OS_V1_ARCHITECTURE.md (Canon-adjacent
architecture document, not a numbered factory/packages/0XX_*.md Core
package - Modules are not part of the Core numbering series). This
file is not a substitute for that document, per the
FRAMEWORK_DOCUMENT_LOCATION_CONVENTION.md pointer convention
(factory/standards/).

Purpose:
    An AI Sales Operating System for a packaging salesperson, built as
    a Module registering with Core via argus.plugins (Package 014).
    Sprint 1 scope: the Lead Workspace foundation only - load leads,
    build a daily work queue, persist session state, resume exactly
    where a previous session ended. Browser automation and the live
    Dynamics sync are explicitly out of scope for Sprint 1.

Responsibilities:
    - Own Sales-specific expertise and workflow: Lead/Contact/Company/
      Campaign/WorkItem domain models, the work queue, session schema.

Non-Responsibilities:
    - This package owns no Core mechanism. Session persistence,
      logging, and connector infrastructure are Core; this Module
      supplies only the schema/content that flows through them.
    - This package is never imported by anything under argus/ that is
      not itself part of argus.modules.sales.

Dependencies:
    argus.plugins (Package 014) - registration.
"""
