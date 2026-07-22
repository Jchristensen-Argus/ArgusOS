# Dev Log

## v0.0.9 – Intent Detection

Today Argus made its first architectural decision.

The Brain now routes requests instead of blindly sending everything to the AI.

Testing revealed a major architectural insight:

Memory stores information.
Knowledge understands information.

This changed the roadmap and led to the design of the Knowledge Engine.
---

## Package 002 – Bootstrap

Argus Factory reconciled two conflicting implementation packages (001_FOUNDATION and 002_BOOTSTRAP, which both targeted the same files with diverging scope). The Architect retired 001 as historical documentation and confirmed 002 as authoritative.

Built the foundational application framework: a dependency injection Container, a minimal Configuration loader, a Logging Service wrapping the standard library, and an Application lifecycle (start/shutdown), wired together by a single `bootstrap()` function. `python main.py` now runs this sequence instead of launching the legacy Shell.

Two things came up worth carrying forward:

Order of initialization matters. LOGGING.md states Logging depends on Configuration, so Configuration loads first and Logging initializes from it — not the other way around.

Configuration Service's own specification lists Event Bus as a required dependency, but Event Bus is out of scope for this package. Resolved by scoping this package's Configuration to a one-time startup load with no change notification; wiring to the Event Bus is deferred until that package exists.

The interactive Shell still exists in the codebase but is no longer started from `main.py`. It predates the Factory architecture and needs to be reintroduced deliberately as an application on top of this foundation, not bypassed around it.

The coding standard was also consolidated: `CODING_STANDARDS.md` and `coding.md` were merged into a single canonical `factory/standards/CODING_STANDARD.md`.

---

## Package 002 – Bootstrap (architecture review correction)

Architecture review caught a real gap: the test suite booted fine in isolation but `python -m unittest` and `python -m unittest discover` found zero tests, and `pytest` wasn't installed in the review environment. Root cause: the tests were written as bare pytest-style functions (`pytest.raises`, the `tmp_path` fixture) with no `unittest.TestCase` classes, and `pytest` was never declared as a project dependency anywhere in the repo. `unittest`'s loader only collects test methods defined on `TestCase` subclasses, so it silently found nothing.

Rewrote all five test files as `unittest.TestCase` classes using only the standard library (`tempfile.TemporaryDirectory` in place of `tmp_path`, `assertRaises` in place of `pytest.raises`), and added `tests/__init__.py`. Verified `python -m unittest`, `python -m unittest discover`, and `python -m unittest discover -s tests` all find and pass the full 21-test suite with no dependencies beyond the standard library, consistent with the coding standard's preference for the standard library over new dependencies.
