# Argus Coding Standards

Version: 1.0
Status: Active

---

# Purpose

These standards define the minimum quality expectations for all production code written for ArgusOS.

They exist to improve readability, maintainability, consistency, and long-term evolution.

---

# General Principles

- Write code for humans first.
- Optimize for clarity over cleverness.
- Favor simple designs.
- Avoid premature optimization.
- Prefer explicit behavior over hidden magic.

---

# Naming

Use descriptive names.

Avoid abbreviations unless universally understood.

Good:

```
calculate_quote()
PackagingSpecification
customer_memory
```

Avoid:

```
calc()
pkgSpec
tmp
```

---

# Single Responsibility

Functions should perform one logical task.

Classes should have one primary purpose.

Large functions should be decomposed into smaller units.

---

# File Organization

Each file should contain one primary concept.

Avoid mixing unrelated functionality.

---

# Documentation

Every public module should include:

- Purpose
- Inputs
- Outputs
- Dependencies

Complex logic should explain *why*, not merely *what*.

---

# Error Handling

Handle expected failures gracefully.

Avoid silent failures.

Return meaningful error information.

Log unexpected conditions when appropriate.

---

# Testing

Every production feature should include tests appropriate to its complexity.

Tests should verify:

- expected behavior
- edge cases
- invalid input
- regressions

---

# Dependencies

Minimize external dependencies.

Prefer the standard library when practical.

New dependencies should have a clear justification.

---

# Backwards Compatibility

Changes to public interfaces require architectural review.

Breaking changes should be deliberate and documented.

---

# Performance

Optimize only after correctness and clarity.

Measure performance before making optimization decisions.

---

# Security

Never expose sensitive information in logs.

Validate external input.

Follow the principle of least privilege.

---

# Code Reviews

Every implementation should answer:

- Is the code correct?
- Is it understandable?
- Is it maintainable?
- Does it follow the specification?
- Does it follow Argus principles?

---

# Guiding Principle

Readable code is easier to improve than clever code.