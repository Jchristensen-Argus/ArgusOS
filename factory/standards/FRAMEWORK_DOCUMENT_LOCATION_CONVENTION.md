# Repository Convention: Framework Document Location

Status: Adopted convention. Not an ADR — this does not modify or reopen ADR-0003 ("Framework Markdown Documents Are Canonical Engineering Artifacts"), it operationalizes it.

---

## The Convention

- Framework documents remain in a single canonical location: `factory/packages/0XX_*.md`. There is exactly one authoritative copy of a package's design rationale, decision history, and verification record.
- Packages never contain duplicated framework documents. No `argus/<package>/README.md`, docstring, or comment block may restate the framework document's content — not the Engineering Decisions section, not the Real-World Examples, not the Repository Verification Note. If it's already written in the framework document, it is not rewritten anywhere else.
- Packages may contain a non-authoritative pointer directing developers to the canonical framework document. This may take the form of a short `DESIGN.md` inside the package directory, or a note in the package's `__init__.py` module docstring — either is acceptable, chosen per package as convenient.
- The pointer must never summarize or duplicate the framework's contents. Its only job is discoverability: telling a developer where to look, not what they'll find there.

## What a Compliant Pointer Looks Like

```
# argus/automation/DESIGN.md

Design rationale, engineering decisions, and verification history for this
package are recorded in factory/packages/041_AUTOMATION_FRAMEWORK.md.
This file is not a substitute for that document.
```

or, as a module docstring:

```python
"""
argus.automation

Design rationale: see factory/packages/041_AUTOMATION_FRAMEWORK.md.
"""
```

## What a Non-Compliant Pointer Looks Like

Anything that restates *why* a decision was made, rather than only stating *where* to find out why:

```
# Not compliant — this restates content that belongs solely in the framework document.

"""
argus.automation

AutomationTrigger defaults to MANUAL because it is both the first-listed
member and the most conservative choice. See factory/packages/041_AUTOMATION_FRAMEWORK.md
for more.
"""
```

The moment a pointer starts explaining a decision instead of locating its explanation, it has become a second, unmaintained copy — the exact failure mode ADR-0003 exists to prevent.

## Rationale, Briefly

This is a direct application of ADR-0003 (framework documents are canonical, not disposable) and Canon ADR-0005 (one concept, one authoritative home) to the question of where files physically live, not just what they say. Two copies of the same design rationale — one in `factory/packages/`, one duplicated into the package itself — will drift the first time either one is updated without the other. A pointer that only says *where*, never *what*, cannot drift, because it has nothing to keep in sync.

## Scope

Applies to all packages going forward. Does not require retroactively adding pointers to the 001–041 packages already delivered, consistent with the general Canon and engineering policy of extending forward rather than revising settled work absent a genuine defect — though adding a pointer to an existing package is a trivial, low-risk addition if convenient to do alongside unrelated future work on that package.
