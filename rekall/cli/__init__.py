# rekall/cli/__init__.py
"""
CLI module - modular command structure.

This package provides the main Typer application and organizes CLI commands
into logical submodules.

Architecture:
    - rekall.cli (this package): Modular CLI structure with re-exports
    - rekall.cli_main: Original monolithic CLI (will be refactored incrementally)

Current State (Facade Pattern):
    All commands currently live in cli_main.py. This package re-exports
    the main `app` for backward compatibility. Future extraction will
    move commands into submodules:

    - core.py: version, config, init, info
    - entries.py: search, add, show, browse, deprecate
    - memory.py: review, stale, generalize
    - knowledge_graph.py: link, unlink, related, graph
    - import_export.py: export, import_archive
    - research.py: research, similar, suggest
    - sources.py: sources_app subcommands
    - inbox.py: inbox_app subcommands
    - staging.py: staging_app subcommands
    - system.py: backup, restore, migrate, embeddings, mcp_server, consolidation

Usage:
    from rekall.cli import app  # Main Typer application
    from rekall.cli import sources_app, inbox_app, staging_app  # Sub-apps
"""

from __future__ import annotations

# Re-export main Typer app and sub-apps from cli_main.py
from rekall.cli_main import (
    app,
    console,
    inbox_app,
    show_banner,
    sources_app,
    staging_app,
)

__all__ = [
    "app",
    "console",
    "inbox_app",
    "show_banner",
    "sources_app",
    "staging_app",
]
