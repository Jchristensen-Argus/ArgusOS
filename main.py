from argus.bootstrap import bootstrap
from module_loader import load_modules


def main() -> None:
    """
    ArgusOS entry point.

    Runs the Package 002 Bootstrap sequence to bring the application to
    a running state, then loads every installed Module (Sprint 1,
    Priority #6 - see module_loader.py) before shutting down cleanly.

    No engine logic (Atlas, Cortex, Hermes, Navigator, Sentinel) runs
    here; that is out of scope for Package 002 - Bootstrap. The
    pre-Factory interactive Shell (argus/shell.py) is intentionally not
    invoked here pending a future implementation package that
    reintegrates it on top of this foundation.
    """
    application = bootstrap()
    try:
        load_modules(application.container)
    finally:
        application.shutdown()


if __name__ == "__main__":
    main()
