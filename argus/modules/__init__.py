"""
argus.modules - Namespace package for all business-specific Argus Modules.

Purpose:
    Hold every Module (Sales, and future Modules such as Ecommerce,
    Amazon, Marketing) as a sibling subpackage. Per the Core/Module/
    Integration taxonomy established for Argus Sales OS V1, this
    package itself contains no code and no shared logic - it is a
    pure namespace. A Module registers with Core via argus.plugins
    (Package 014); nothing in argus.modules is imported by anything
    under argus/ that is not itself a Module.

Responsibilities:
    - Serve as the namespace root under which Modules live.

Non-Responsibilities:
    - This package defines no behavior, no shared base classes, and
      no cross-Module utilities. A mechanism needed by more than one
      Module belongs in Core, not here (Cognitive Architecture, CA-11).

Dependencies:
    None.
"""
