# rekall/ui/__init__.py
"""
TUI module - modular Textual interface structure.

This package provides the Terminal User Interface for Rekall using Textual.

Architecture:
    - rekall.ui (this package): Modular TUI structure with re-exports
    - rekall.tui_main: Original monolithic TUI (will be refactored incrementally)

Current State (Facade Pattern):
    All TUI components currently live in tui_main.py. This package re-exports
    the main functions for backward compatibility. Future extraction will
    move components into submodules:

    - theme.py: Colors, CSS, banner
    - helpers.py: Utility functions
    - app.py: Main application entry point
    - widgets/: Reusable Textual widgets
    - screens/: Full-screen Textual Apps

Usage:
    from rekall.ui import run_tui  # Main entry point
    from rekall.ui import RekallMenuApp  # Main menu app
"""

from __future__ import annotations

# Re-export main functions from tui_main.py
from rekall.tui_main import (
    RekallMenuApp,
    run_tui,
)

__all__ = [
    "RekallMenuApp",
    "run_tui",
]
