# ADR-0003: Framework Markdown Documents Are Canonical Engineering Artifacts

## Status

Accepted

---

## Date

2026-07-27

---

## Context

`factory/packages/0XX_*.md` and related framework documentation (design rationale, engineering-decision narratives, repository verification notes) have, to date, existed in an ambiguous position relative to the source code and tests they describe. Nothing established whether these files were the authoritative record of a package's design, or a disposable summary that could be regenerated from `argus/*/` and the test suite whenever convenient.

This question surfaced directly while reviewing the Argus Canon (Document I, "The Constitution of Argus," and Document III, "The Reasoning Engine" — see Canon ADR-0008 for the numbering), both of which draw a hard line between preserving a conclusion and preserving the reasoning that produced it. Constitutional Principle CO-06 (Learning) requires organizations to "preserve not only what was decided, but why it was decided, what assumptions were made, what outcomes followed." Constitutional Principle CO-07 (Transparency) states "reasoning that cannot be examined cannot be improved." Document III's Chapter Seven goes further, specifying that every recommendation must carry two inseparable payloads — a Decision Payload (what) and a Reasoning Payload (why) — because neither is complete without the other.

Applying that same standard to `factory/packages/*.md` produces an unambiguous answer. Inspection of these files (see, for example, `041_AUTOMATION_FRAMEWORK.md`'s "Engineering Decisions" section, or `039_DECISION_FRAMEWORK.md`'s full naming-collision narrative) shows they contain two distinct categories of content:

- **Mechanically derivable facts** — file lists, module names, dependency edges, test counts, coverage percentages. These can be reconstructed at any time by reading the code and running the test suite.
- **Non-derivable reasoning** — why a given default was chosen over the alternative, why a naming collision was resolved one way rather than another, what was verified before a package shipped and by what method, which design options were considered and rejected. None of this exists anywhere except in the document itself. Source code records the outcome of a decision; it does not record the decision.

Treating these files as transient build artifacts — safe to delete and regenerate from source — would permanently destroy the second category with no path to recovery, while the codebase itself would continue to build and pass tests without any visible sign that anything had been lost.

---

## Decision

Framework Markdown documents (`factory/packages/*.md` and equivalent design-rationale documentation) are canonical engineering artifacts, not build output.

Packages and generated code are **implementations of the specifications and decisions these documents record** — not replacements for them, and not authoritative over them regarding intent. Where source code and its accompanying framework document appear to disagree about *why* something was built a certain way, the framework document is the source of truth for intent; a code change that contradicts its own framework document's stated rationale should be treated as a signal that either the document needs a deliberate, recorded update, or the code change itself needs review — not as license to let the document silently go stale.

Going forward, ArgusOS's knowledge shall be organized around three distinct, separately preserved concerns, consistent with the Argus Canon's own Reasoning/Judgment distinction (Document III, Chapter Ten) and Decision/Reasoning Payload architecture (Document III, Chapter Seven):

- **Reasoning** — why a decision was made: the alternatives considered, the constraints weighed, the evidence available at the time.
- **Decision** — what was decided: the concrete choice made, stated plainly, independent of its justification.
- **Implementation** — how the decision was realized: the actual code, tests, and configuration.

These three shall remain separable throughout ArgusOS. Framework documents are the home of Reasoning and Decision. Source code and tests are the home of Implementation. A framework document that only restates what the code already shows, without capturing why, has not fulfilled its purpose.

---

## Consequences

Positive

- Design rationale, naming-collision resolutions, and engineering tradeoffs — which took real effort to work through and are expensive to reconstruct — are permanently protected rather than left one "clean up the docs" pass away from being lost.
- ArgusOS's own engineering practice becomes consistent with the standard the Argus Canon sets for the product itself: an organization (in this case, the Argus Factory) that preserves the reasoning behind its own decisions, not merely their outcomes.
- Future packages have a clear structural expectation: a framework document isn't complete until it answers *why*, not just *what* and *how*.

Trade-offs

- Framework documents now carry an explicit maintenance obligation — they must be kept honest against the code they describe, rather than being treated as a one-time snapshot from the day a package shipped.
- Some existing framework documents blend all three concerns (Reasoning, Decision, Implementation-adjacent facts like test counts) in a single undifferentiated narrative. This ADR does not require retroactively restructuring existing package documents; it establishes the policy for how they are treated and how future documents should be structured, consistent with the general Canon policy of extending rather than revising existing artifacts absent a genuine defect.

---

## Related Documents

- Argus Canon, Document III: The Reasoning Engine — Chapter Seven (Decision Payload / Reasoning Payload), Chapter Ten (Reasoning/Judgment distinction)
- Argus Canon, Document I: The Constitution of Argus — CO-06 (Learning), CO-07 (Transparency)
- Argus Canon ADR Log — ADR-0005 (One Concept, One Authoritative Home), ADR-0008 (Canon document numbering)
- `design/decisions/0001_ARCHITECTURE_BASELINE.md`
- `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`
