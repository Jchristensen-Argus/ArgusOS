# Argus Factory Roadmap

## Phase 1 — Foundation
- [x] Architecture
- [x] Specifications
- [x] Coding Standards
- [x] ADR Process
- [x] Implementation Packages
- [x] Bootstrap
- [ ] Configuration (minimal loader shipped with Bootstrap; full CONFIGURATION.md service still pending)
- [ ] Logging (minimal service shipped with Bootstrap; full LOGGING.md service still pending)
- [x] Event Bus
- [x] Service Registry
- [x] Dependency Injection
- [x] Lifecycle (Application start/shutdown, Package 002)
- [x] Service Lifecycle Framework (IService, LifecycleManager, Package 005)
- [x] Knowledge Service (KnowledgeRecord, IKnowledgeStorage/IKnowledgeService, JSONKnowledgeStorage, KnowledgeService, Package 006)
- [x] Memory Service (MemoryRecord, IMemoryStorage/IMemoryService, JSONMemoryStorage, MemoryService, Package 007)

---

## Phase 2 — Core Engines

- [x] Memory (short-term, expiry-aware working memory shipped as a Foundation-phase core service, Package 007; see Phase 1 above)
- [ ] Atlas (blocked on: none currently — Memory Service, its one Required Dependency, now exists)
- [ ] Cortex (blocked on: no specification file exists yet in design/specifications/)
- [ ] Hermes (blocked on: Cortex)
- [ ] Navigator (blocked on: Cortex, Hermes, Scheduler)
- [ ] Scheduler (blocked on: Navigator — see design/specifications/SCHEDULER.md's Required Dependencies)
- [ ] Sentinel (no blockers — Event Bus, Logging, Configuration all exist; not yet selected as a package, see factory/packages/007_MEMORY_SERVICE.md)

---

## Phase 3 — Applications

- [ ] Packaging
- [ ] Trading
- [ ] Realty
- [ ] Tallow

---

## Phase 4 — Intelligence

- [ ] Multi-agent coordination
- [ ] Long-term memory
- [ ] Autonomous planning
- [ ] Continuous learning