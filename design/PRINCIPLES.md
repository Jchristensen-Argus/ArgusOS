# ARGUS Engineering Principles

Version: 1.0  
Status: Active

---

# Purpose

These principles govern every architectural and engineering decision made within the Argus ecosystem.

Unlike implementation details, these principles are intended to remain stable over the lifetime of the project.

Any change to these principles requires deliberate human review.

---

# Principle 1
## Architecture Before Implementation

Architecture is the primary artifact.

Code is an implementation artifact.

Every subsystem must begin with an approved design before implementation starts.

---

# Principle 2
## Single Responsibility

Every subsystem has one primary responsibility.

If a subsystem begins solving multiple unrelated problems, it should be divided into smaller components.

---

# Principle 3
## Stable Interfaces

Public interfaces should remain stable.

Internal implementations may evolve freely as long as the public contract remains intact.

---

# Principle 4
## Human Judgment First

AI assists.

Humans decide.

Architectural decisions require human approval.

AI may recommend changes but never approve them.

---

# Principle 5
## Knowledge Compounds

Knowledge should accumulate.

Information should not be destroyed simply because it has been replaced.

Historical knowledge has value.

Argus should preserve history whenever practical.

---

# Principle 6
## Local First

Whenever practical:

- data remains local
- reasoning remains local
- automation remains local

Cloud services extend capability but should not become unnecessary dependencies.

---

# Principle 7
## Explicit Responsibilities

Every subsystem must clearly define:

- Purpose
- Responsibilities
- Non-responsibilities
- Inputs
- Outputs
- Dependencies

Ambiguous ownership creates architectural debt.

---

# Principle 8
## Build for Evolution

Software should become easier to improve over time.

Short-term convenience should never create long-term complexity.

Every implementation should increase future engineering leverage.

---

# Principle 9
## Simplicity Wins

Choose the simplest architecture that satisfies current requirements.

Avoid solving problems that do not yet exist.

Complexity must be justified.

---

# Principle 10
## Documentation is Source Code

Design documents are first-class engineering artifacts.

Documentation is not optional.

Architecture documents are reviewed with the same care as software.

---

# Principle 11
## Testing is Part of Development

Software is not complete until it can be verified.

Every subsystem should define how correctness is measured.

Testing is designed alongside implementation—not after it.

---

# Principle 12
## Continuous Improvement

Every sprint should improve one of two things:

- ArgusOS
- Argus Factory

The engineering organization should become more capable with every iteration.

---

# Engineering Question

Before approving any implementation, ask:

Does this decision make Argus easier to improve five years from now?

If the answer is no, reconsider the design.