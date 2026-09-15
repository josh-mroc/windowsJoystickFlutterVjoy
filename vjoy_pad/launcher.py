"""Dependency-aware launcher for the vJoy touchpad application."""

from __future__ import annotations

import importlib
import sys


def pygame_install_message() -> str:
    """Return installation guidance that targets the active interpreter."""
    return (
        "pygame is not installed for this Python interpreter.\n"
        "This project uses the 'pygame-ce' package, which is imported as 'pygame'.\n\n"
        f'Install the project dependencies with:\n  "{sys.executable}" -m pip install -r requirements.txt\n\n'
        "If you are using VS Code, select the same virtual environment with "
        "Python: Select Interpreter, then run the application again."
    )


def main() -> None:
    """Load the UI lazily so a missing dependency produces useful guidance."""
    try:
        app = importlib.import_module("vjoy_pad.app")
    except ModuleNotFoundError as exc:
        if exc.name != "pygame":
            raise
        raise SystemExit(pygame_install_message()) from None
    app.main()
