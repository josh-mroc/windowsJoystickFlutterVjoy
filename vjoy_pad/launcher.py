"""Dependency-aware launcher for the vJoy touchpad application."""

from __future__ import annotations

import importlib
import sys


def _uses_uv_managed_python(executable: str) -> bool:
    """Return whether *executable* looks like an interpreter installed by uv."""
    normalized = executable.replace("\\", "/").casefold()
    return "/uv/python/" in normalized


def pygame_install_message() -> str:
    """Return installation guidance that targets the active interpreter."""
    if _uses_uv_managed_python(sys.executable):
        install_command = (
            "uv-managed Python installations may not include pip. Install with uv:\n"
            f'  uv pip install --python "{sys.executable}" -r requirements.txt\n\n'
            "Alternatively, create and select a project virtual environment:\n"
            "  uv venv .venv\n"
            "  uv pip install --python .venv -r requirements.txt"
        )
    else:
        install_command = (
            "Install the project dependencies with:\n"
            f'  "{sys.executable}" -m pip install -r requirements.txt'
        )

    return (
        "pygame is not installed for this Python interpreter.\n"
        "This project uses the 'pygame-ce' package, which is imported as 'pygame'.\n\n"
        f"{install_command}\n\n"
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
