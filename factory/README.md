# Argus Factory

Version: 1.0  
Status: Active

---

# Welcome

Argus Factory is the engineering organization responsible for designing, implementing, testing, reviewing, documenting, and evolving ArgusOS.

This repository is specification-driven. Every implementation begins with a design, follows a defined workflow, and is reviewed against established engineering principles.

If you are contributing to ArgusOS, start here.

---

# Read These Documents First

Read the following documents in order:

1. `design/ARGUS.md`
2. `design/PRINCIPLES.md`
3. `design/FACTORY.md`
4. `factory/workflow.md`

These documents define the project's mission, engineering philosophy, organizational structure, and development lifecycle.

---

# Repository Structure

```
design/
    Governing documents and subsystem specifications

factory/
    Engineering process, standards, templates, and prompts

agents/
    Runtime AI agents

memory/
    Long-term memory and knowledge resources

projects/
    Project-specific work

tests/
    Automated verification
```

As the project evolves, additional directories may be added while preserving this overall organization.

---

# Development Process

Every feature follows the same lifecycle:

```
Vision
→ Specification
→ Architecture Review
→ Implementation
→ Testing
→ Documentation
→ Review
→ Git Commit
→ Release
```

Do not skip steps without explicit approval.

---

# Engineering Standards

Every contribution should:

- Solve one clearly defined problem.
- Preserve architectural simplicity.
- Follow approved specifications.
- Include appropriate tests.
- Update documentation when behavior changes.
- Leave the repository in a better state than it was found.

---

# Definition of Done

A task is complete only when:

- The specification has been approved.
- The implementation matches the specification.
- Tests pass.
- Documentation has been updated.
- Architectural review is complete.
- The work is ready to merge.

---

# Guiding Principle

The goal is not to produce more code.

The goal is to produce a system that becomes easier to improve over time.