"""
The Argus Module Loader (Sprint 1, Priority #6).

Purpose:
    Bring installed Modules into a running Argus instance after Core
    has booted. This is the composition-root addition the Module
    Loading investigation (conducted before the Spreadsheet Importer
    slice) recommended and deliberately deferred: "a thin Module
    Loader - hardcoded module list (no dynamic discovery yet), each
    Module exposes a register(container) entry point, loader lives at
    the repo root alongside main.py (never inside argus/, since it
    must import Modules by construction and Core must not)." That
    recommendation is implemented here, unchanged, now that Priority
    #6 (proving the first complete vertical) has arrived.

Why This File Sits At The Repo Root, Not Inside argus/:
    Cognitive Architecture CA-10: "Core remains domain-agnostic,
    permanently. It never imports, references, or assumes a Module's...
    concepts." This file imports argus.modules.sales.registration by
    name - if it lived inside argus/, that would be Core importing a
    Module, which CA-10 forbids outright. Living beside main.py (which
    already sits outside the Core/Module boundary as the entry point)
    keeps that boundary intact: Core (argus/) never knows Modules
    exist; the composition root (main.py + module_loader.py) is the
    one place in the whole system allowed to know about both.

Hardcoded List, Not Dynamic Discovery - Deliberately, Still:
    MODULE_REGISTRARS below is a plain tuple of import paths, edited by
    hand when a new Module is added. Per the original investigation,
    dynamic discovery (scanning a directory, entry_points, or similar)
    is future work, not a Sprint 1 need - Sales is still the only
    Module that exists. Do not build discovery machinery for a second
    Module that doesn't exist yet.

What load_modules() Does, In Order:
    1. Calls each registrar's register(container) function, in list
       order - this is where each Module registers its own Plugin,
       constructs its own services, and registers its own Workflows
       (see argus/modules/sales/registration.py for what Sales's
       register() specifically does).
    2. Brings the shared "workflow_engine" Core service to RUNNING
       (initialize() then start()) if it is not already - done here,
       once, rather than by any individual Module's register(),
       because the Workflow Engine is a shared Core resource multiple
       Modules may register Workflows with; only the loader that
       finishes wiring every Module knows it is safe to start it.

Responsibilities:
    - MODULE_REGISTRARS: the hardcoded list of installed Modules'
      register(container) callables.
    - load_modules(container): call each registrar, then start the
      Workflow Engine.

Non-Responsibilities:
    - This file does not construct the Container or run bootstrap() -
      see main.py, which calls bootstrap() first and passes its
      resulting application.container in here.
    - This file does not discover Modules dynamically - see the note
      above.

Dependencies:
    argus.container (Container - typing only), argus.lifecycle
    (LifecycleState - typing only), argus.modules.sales.registration
    (the only Module registrar that exists as of Sprint 1).
"""

from typing import Callable, Sequence

from argus.container import Container
from argus.lifecycle.lifecycle import LifecycleState
from argus.modules.sales.registration import register as register_sales

#: Every installed Module's register(container) entry point, in the
#: order they should be loaded. Add a new Module by adding its
#: register function here - nothing else in this file changes.
MODULE_REGISTRARS: Sequence[Callable[[Container], None]] = (register_sales,)


def load_modules(container: Container) -> None:
    """
    Register every installed Module with an already-booted Argus
    instance, then bring the shared Workflow Engine to RUNNING.

    Parameters:
        container: application.container from an already-called
            argus.bootstrap.bootstrap().
    """
    for register in MODULE_REGISTRARS:
        register(container)

    workflow_engine = container.resolve("workflow_engine")
    if workflow_engine.status() == LifecycleState.CREATED:
        workflow_engine.initialize()
        workflow_engine.start()
